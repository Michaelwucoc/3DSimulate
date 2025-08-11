#!/usr/bin/env python3
"""
深度分析和场景可视化工具
支持：
1. 场景和相机可视化 (viser, Open3D, scenepic)
2. COLMAP处理和稀疏点云生成
3. 单目深度估计 (DepthAnything v2, Depth-Pro)
4. Normalized depth vs Metric depth 分析
"""

import os
import sys
import argparse
import numpy as np
import cv2
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union
import logging

# 3D可视化库
try:
    import viser
    HAS_VISER = True
except ImportError:
    HAS_VISER = False
    print("Warning: viser not installed. Run: pip install viser")

try:
    import open3d as o3d
    HAS_OPEN3D = True
except ImportError:
    HAS_OPEN3D = False
    print("Warning: Open3D not installed. Run: pip install open3d")

try:
    import scenepic as sp
    HAS_SCENEPIC = True
except ImportError:
    HAS_SCENEPIC = False
    print("Warning: scenepic not installed. Run: pip install scenepic")

# 深度估计库
try:
    import torch
    from transformers import pipeline
    HAS_DEPTH_ANYTHING = True
except ImportError:
    HAS_DEPTH_ANYTHING = False
    print("Warning: transformers not installed for DepthAnything v2")

try:
    # Depth-Pro 需要从GitHub安装
    # pip install git+https://github.com/apple/depth-pro.git
    import depth_pro
    HAS_DEPTH_PRO = True
except ImportError:
    HAS_DEPTH_PRO = False
    print("Warning: depth-pro not installed")

# COLMAP
import subprocess
import tempfile

class CameraData:
    """相机数据结构"""
    def __init__(self, image_path: str, depth_path: str, intrinsics: np.ndarray, 
                 extrinsics: np.ndarray, camera_id: int = 0):
        self.image_path = image_path
        self.depth_path = depth_path
        self.intrinsics = intrinsics  # 3x3 内参矩阵
        self.extrinsics = extrinsics  # 4x4 外参矩阵 (camera to world)
        self.camera_id = camera_id
        
        # 加载图像和深度
        self.image = cv2.imread(image_path)
        self.image_rgb = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        
        # 加载深度图 (假设是.npy或.png格式)
        if depth_path.endswith('.npy'):
            self.depth = np.load(depth_path)
        else:
            depth_img = cv2.imread(depth_path, cv2.IMREAD_ANYDEPTH)
            self.depth = depth_img.astype(np.float32)
            
        self.height, self.width = self.image.shape[:2]

class DepthAnalyzer:
    """深度分析主类"""
    
    def __init__(self, data_dir: str, output_dir: str = "output"):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.cameras = []
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        """设置日志"""
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        return logger
        
    def load_camera_data(self, image_dir: str, depth_dir: str, 
                        intrinsics_file: str, extrinsics_file: str):
        """加载相机数据"""
        self.logger.info("Loading camera data...")
        
        # 加载内参
        intrinsics = np.load(intrinsics_file) if intrinsics_file.endswith('.npy') else \
                    json.load(open(intrinsics_file))
        
        # 加载外参
        extrinsics = np.load(extrinsics_file) if extrinsics_file.endswith('.npy') else \
                    json.load(open(extrinsics_file))
        
        # 获取图像和深度文件列表
        image_files = sorted(list(Path(image_dir).glob("*.jpg")) + 
                           list(Path(image_dir).glob("*.png")))
        depth_files = sorted(list(Path(depth_dir).glob("*.npy")) + 
                           list(Path(depth_dir).glob("*.png")))
        
        assert len(image_files) == len(depth_files), "图像和深度文件数量不匹配"
        
        # 创建相机对象
        for i, (img_path, depth_path) in enumerate(zip(image_files, depth_files)):
            if isinstance(intrinsics, dict):
                K = np.array(intrinsics[f'camera_{i}']) if f'camera_{i}' in intrinsics else \
                    np.array(intrinsics['K'])
            else:
                K = intrinsics[i] if intrinsics.ndim == 3 else intrinsics
                
            if isinstance(extrinsics, dict):
                T = np.array(extrinsics[f'camera_{i}']) if f'camera_{i}' in extrinsics else \
                    np.array(extrinsics[i])
            else:
                T = extrinsics[i] if extrinsics.ndim == 3 else extrinsics
                
            camera = CameraData(str(img_path), str(depth_path), K, T, i)
            self.cameras.append(camera)
            
        self.logger.info(f"Loaded {len(self.cameras)} cameras")
        
    def visualize_with_viser(self, port: int = 8080):
        """使用Viser可视化场景和相机"""
        if not HAS_VISER:
            self.logger.error("Viser not available")
            return
            
        self.logger.info(f"Starting Viser server on port {port}")
        
        server = viser.ViserServer(port=port)
        
        # 添加相机可视化
        for i, camera in enumerate(self.cameras):
            # 相机位置 (从外参矩阵提取)
            camera_pos = camera.extrinsics[:3, 3]
            camera_rot = camera.extrinsics[:3, :3]
            
            # 添加相机frustum
            server.scene.add_camera_frustum(
                name=f"camera_{i}",
                fov=60.0,  # 可以从内参计算
                aspect=camera.width / camera.height,
                scale=0.3,
                position=camera_pos,
                wxyz=self._rotation_matrix_to_quaternion(camera_rot)
            )
            
            # 添加图像
            server.scene.add_image(
                name=f"image_{i}",
                image=camera.image_rgb,
                position=camera_pos + np.array([0, 0, 0.5]),
                wxyz=self._rotation_matrix_to_quaternion(camera_rot)
            )
            
        # 从深度图生成点云
        points = self._generate_point_cloud_from_depth()
        if len(points) > 0:
            server.scene.add_point_cloud(
                name="depth_pointcloud",
                points=points[:, :3],
                colors=(points[:, 3:6] * 255).astype(np.uint8) if points.shape[1] >= 6 else None
            )
            
        self.logger.info(f"Viser visualization running at http://localhost:{port}")
        input("Press Enter to stop the server...")
        
    def visualize_with_open3d(self):
        """使用Open3D可视化场景和相机"""
        if not HAS_OPEN3D:
            self.logger.error("Open3D not available")
            return
            
        self.logger.info("Creating Open3D visualization...")
        
        vis = o3d.visualization.Visualizer()
        vis.create_window("Camera Scene Visualization", width=1200, height=800)
        
        # 添加相机模型
        for i, camera in enumerate(self.cameras):
            # 创建相机frustum
            frustum = self._create_camera_frustum_open3d(camera)
            frustum.paint_uniform_color([1.0, 0.0, 0.0] if i == 0 else [0.0, 0.0, 1.0])
            vis.add_geometry(frustum)
            
        # 从深度图生成点云
        point_cloud = self._generate_open3d_point_cloud()
        if point_cloud is not None:
            vis.add_geometry(point_cloud)
            
        # 添加坐标系
        coordinate_frame = o3d.geometry.TriangleMesh.create_coordinate_frame(size=1.0)
        vis.add_geometry(coordinate_frame)
        
        vis.run()
        vis.destroy_window()
        
    def visualize_with_scenepic(self):
        """使用ScenePic可视化场景和相机"""
        if not HAS_SCENEPIC:
            self.logger.error("ScenePic not available")
            return
            
        self.logger.info("Creating ScenePic visualization...")
        
        scene = sp.Scene()
        
        # 创建canvas
        canvas = scene.create_canvas_3d(width=1200, height=800)
        
        # 添加相机
        for i, camera in enumerate(self.cameras):
            # 相机位置和方向
            pos = camera.extrinsics[:3, 3]
            rot = camera.extrinsics[:3, :3]
            
            # 创建相机模型
            camera_mesh = self._create_camera_mesh_scenepic(camera)
            canvas.create_mesh(f"camera_{i}", camera_mesh)
            
        # 添加点云
        points = self._generate_point_cloud_from_depth()
        if len(points) > 0:
            canvas.create_mesh("pointcloud", points)
            
        # 保存HTML文件
        output_path = self.output_dir / "scenepic_visualization.html"
        scene.save_as_html(str(output_path))
        self.logger.info(f"ScenePic visualization saved to {output_path}")
        
    def run_colmap(self, output_dir: str = None):
        """运行COLMAP进行SfM重建"""
        if output_dir is None:
            output_dir = self.output_dir / "colmap"
        else:
            output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        self.logger.info("Running COLMAP...")
        
        # 创建COLMAP输入结构
        images_dir = output_dir / "images"
        images_dir.mkdir(exist_ok=True)
        
        # 复制图像到COLMAP目录
        for i, camera in enumerate(self.cameras):
            dst_path = images_dir / f"image_{i:04d}.jpg"
            if not dst_path.exists():
                cv2.imwrite(str(dst_path), camera.image)
                
        # 创建数据库
        database_path = output_dir / "database.db"
        
        try:
            # Feature extraction
            cmd = [
                "colmap", "feature_extractor",
                "--database_path", str(database_path),
                "--image_path", str(images_dir),
            ]
            subprocess.run(cmd, check=True)
            
            # Feature matching
            cmd = [
                "colmap", "exhaustive_matcher",
                "--database_path", str(database_path),
            ]
            subprocess.run(cmd, check=True)
            
            # Sparse reconstruction
            sparse_dir = output_dir / "sparse"
            sparse_dir.mkdir(exist_ok=True)
            
            cmd = [
                "colmap", "mapper",
                "--database_path", str(database_path),
                "--image_path", str(images_dir),
                "--output_path", str(sparse_dir),
            ]
            subprocess.run(cmd, check=True)
            
            self.logger.info(f"COLMAP reconstruction completed: {sparse_dir}")
            
            # 加载COLMAP结果并与depth对比
            self._compare_colmap_with_depth(sparse_dir / "0")
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"COLMAP failed: {e}")
        except FileNotFoundError:
            self.logger.error("COLMAP not found. Please install COLMAP first.")
            
    def estimate_monocular_depth(self, method: str = "depthanything_v2"):
        """单目深度估计"""
        self.logger.info(f"Running monocular depth estimation with {method}")
        
        if method == "depthanything_v2" and HAS_DEPTH_ANYTHING:
            self._estimate_depth_anything_v2()
        elif method == "depth_pro" and HAS_DEPTH_PRO:
            self._estimate_depth_pro()
        else:
            self.logger.error(f"Method {method} not available")
            
    def _estimate_depth_anything_v2(self):
        """使用DepthAnything v2估计深度"""
        # 加载DepthAnything v2模型
        pipe = pipeline(task="depth-estimation", 
                       model="depth-anything/Depth-Anything-V2-Small-hf")
        
        estimated_depths = []
        
        for i, camera in enumerate(self.cameras):
            self.logger.info(f"Processing image {i+1}/{len(self.cameras)}")
            
            # 估计深度
            result = pipe(camera.image_rgb)
            estimated_depth = np.array(result["depth"])
            
            # 保存结果
            output_path = self.output_dir / f"depthanything_v2_{i:04d}.npy"
            np.save(output_path, estimated_depth)
            
            estimated_depths.append(estimated_depth)
            
            # 比较with ground truth
            self._compare_depths(camera.depth, estimated_depth, 
                               f"GT vs DepthAnything V2 - Image {i}")
                               
        return estimated_depths
        
    def _estimate_depth_pro(self):
        """使用Depth-Pro估计深度"""
        estimated_depths = []
        
        for i, camera in enumerate(self.cameras):
            self.logger.info(f"Processing image {i+1}/{len(self.cameras)} with Depth-Pro")
            
            # 使用Depth-Pro估计深度
            depth, info = depth_pro.predict(camera.image_rgb)
            
            # 保存结果
            output_path = self.output_dir / f"depth_pro_{i:04d}.npy"
            np.save(output_path, depth)
            
            estimated_depths.append(depth)
            
            # 比较with ground truth
            self._compare_depths(camera.depth, depth,
                               f"GT vs Depth-Pro - Image {i}")
                               
        return estimated_depths
        
    def _compare_depths(self, gt_depth: np.ndarray, pred_depth: np.ndarray, title: str):
        """比较深度图"""
        import matplotlib.pyplot as plt
        
        # 归一化到相同范围进行比较
        gt_norm = (gt_depth - gt_depth.min()) / (gt_depth.max() - gt_depth.min())
        pred_norm = (pred_depth - pred_depth.min()) / (pred_depth.max() - pred_depth.min())
        
        # 计算误差
        mae = np.mean(np.abs(gt_norm - pred_norm))
        rmse = np.sqrt(np.mean((gt_norm - pred_norm) ** 2))
        
        # 可视化
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        
        axes[0].imshow(gt_norm, cmap='viridis')
        axes[0].set_title('Ground Truth (Normalized)')
        axes[0].axis('off')
        
        axes[1].imshow(pred_norm, cmap='viridis')
        axes[1].set_title('Predicted (Normalized)')
        axes[1].axis('off')
        
        error_map = np.abs(gt_norm - pred_norm)
        im = axes[2].imshow(error_map, cmap='hot')
        axes[2].set_title(f'Error Map\nMAE: {mae:.4f}, RMSE: {rmse:.4f}')
        axes[2].axis('off')
        
        plt.colorbar(im, ax=axes[2])
        plt.suptitle(title)
        plt.tight_layout()
        
        # 保存结果
        output_path = self.output_dir / f"{title.replace(' ', '_').replace('-', '_')}.png"
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"Depth comparison saved: {output_path}")
        self.logger.info(f"MAE: {mae:.4f}, RMSE: {rmse:.4f}")
        
    def analyze_depth_characteristics(self):
        """分析深度特征：normalized vs metric"""
        self.logger.info("Analyzing depth characteristics...")
        
        import matplotlib.pyplot as plt
        
        fig, axes = plt.subplots(2, 4, figsize=(20, 10))
        
        for i, camera in enumerate(self.cameras[:4]):  # 只分析前4个相机
            depth = camera.depth
            
            # 统计信息
            min_depth = np.min(depth[depth > 0])
            max_depth = np.max(depth)
            mean_depth = np.mean(depth[depth > 0])
            
            # 原始深度分布
            axes[0, i].hist(depth[depth > 0].flatten(), bins=50, alpha=0.7)
            axes[0, i].set_title(f'Camera {i} - Metric Depth\n'
                               f'Min: {min_depth:.2f}, Max: {max_depth:.2f}, Mean: {mean_depth:.2f}')
            axes[0, i].set_xlabel('Depth Value')
            axes[0, i].set_ylabel('Frequency')
            
            # 归一化深度分布
            depth_norm = (depth - min_depth) / (max_depth - min_depth)
            axes[1, i].hist(depth_norm[depth > 0].flatten(), bins=50, alpha=0.7, color='orange')
            axes[1, i].set_title(f'Camera {i} - Normalized Depth\n'
                               f'Range: [0, 1]')
            axes[1, i].set_xlabel('Normalized Depth Value')
            axes[1, i].set_ylabel('Frequency')
            
        plt.tight_layout()
        output_path = self.output_dir / "depth_characteristics_analysis.png"
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"Depth characteristics analysis saved: {output_path}")
        
    # 辅助函数
    def _rotation_matrix_to_quaternion(self, R):
        """旋转矩阵转四元数"""
        # 简化实现，实际可使用scipy.spatial.transform.Rotation
        trace = np.trace(R)
        if trace > 0:
            s = np.sqrt(trace + 1.0) * 2
            w = 0.25 * s
            x = (R[2, 1] - R[1, 2]) / s
            y = (R[0, 2] - R[2, 0]) / s
            z = (R[1, 0] - R[0, 1]) / s
        else:
            # 处理其他情况...
            w, x, y, z = 1, 0, 0, 0
        return np.array([w, x, y, z])
        
    def _generate_point_cloud_from_depth(self):
        """从深度图生成点云"""
        all_points = []
        
        for camera in self.cameras[:2]:  # 限制点云数量
            depth = camera.depth
            image = camera.image_rgb
            K = camera.intrinsics
            T = camera.extrinsics
            
            # 生成像素坐标
            h, w = depth.shape
            u, v = np.meshgrid(np.arange(w), np.arange(h))
            
            # 有效深度mask
            valid_mask = depth > 0
            
            if np.sum(valid_mask) == 0:
                continue
                
            # 提取有效点
            u_valid = u[valid_mask]
            v_valid = v[valid_mask]
            z_valid = depth[valid_mask]
            
            # 反投影到3D
            x = (u_valid - K[0, 2]) * z_valid / K[0, 0]
            y = (v_valid - K[1, 2]) * z_valid / K[1, 1]
            
            # 相机坐标系中的点
            points_cam = np.column_stack([x, y, z_valid, np.ones(len(x))])
            
            # 转换到世界坐标系
            points_world = (T @ points_cam.T).T[:, :3]
            
            # 添加颜色
            colors = image[valid_mask] / 255.0
            
            # 下采样
            n_points = len(points_world)
            if n_points > 10000:
                indices = np.random.choice(n_points, 10000, replace=False)
                points_world = points_world[indices]
                colors = colors[indices]
                
            points_with_colors = np.column_stack([points_world, colors])
            all_points.append(points_with_colors)
            
        if all_points:
            return np.vstack(all_points)
        else:
            return np.array([])
            
    def _generate_open3d_point_cloud(self):
        """生成Open3D点云"""
        points = self._generate_point_cloud_from_depth()
        if len(points) == 0:
            return None
            
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points[:, :3])
        if points.shape[1] >= 6:
            pcd.colors = o3d.utility.Vector3dVector(points[:, 3:6])
            
        return pcd
        
    def _create_camera_frustum_open3d(self, camera: CameraData, scale: float = 0.3):
        """创建相机frustum几何体"""
        # 简化的frustum创建
        lines = [
            [0, 1], [0, 2], [0, 3], [0, 4],  # 从原点到4个角点
            [1, 2], [2, 3], [3, 4], [4, 1]   # 矩形边框
        ]
        
        # frustum顶点 (相机坐标系)
        vertices = np.array([
            [0, 0, 0],      # 相机中心
            [-scale, -scale, scale],  # 左下
            [scale, -scale, scale],   # 右下
            [scale, scale, scale],    # 右上
            [-scale, scale, scale]    # 左上
        ])
        
        # 转换到世界坐标系
        vertices_homo = np.column_stack([vertices, np.ones(len(vertices))])
        vertices_world = (camera.extrinsics @ vertices_homo.T).T[:, :3]
        
        line_set = o3d.geometry.LineSet()
        line_set.points = o3d.utility.Vector3dVector(vertices_world)
        line_set.lines = o3d.utility.Vector2iVector(lines)
        
        return line_set
        
    def _create_camera_mesh_scenepic(self, camera: CameraData):
        """创建ScenePic相机模型"""
        # 简化实现
        return {"vertices": [], "faces": []}
        
    def _compare_colmap_with_depth(self, colmap_dir: Path):
        """比较COLMAP结果与深度图"""
        self.logger.info("Comparing COLMAP sparse reconstruction with depth maps...")
        
        try:
            # 读取COLMAP点云 (假设存在points3D.txt)
            points3d_file = colmap_dir / "points3D.txt"
            if not points3d_file.exists():
                self.logger.warning("COLMAP points3D.txt not found")
                return
                
            # 简化的COLMAP点云读取
            colmap_points = []
            with open(points3d_file, 'r') as f:
                for line in f:
                    if line.startswith('#'):
                        continue
                    parts = line.strip().split()
                    if len(parts) >= 6:
                        x, y, z = map(float, parts[1:4])
                        r, g, b = map(int, parts[4:7])
                        colmap_points.append([x, y, z, r/255.0, g/255.0, b/255.0])
                        
            if colmap_points:
                colmap_points = np.array(colmap_points)
                self.logger.info(f"Loaded {len(colmap_points)} COLMAP points")
                
                # 可视化对比 (这里可以添加更详细的对比分析)
                if HAS_OPEN3D:
                    # COLMAP点云
                    colmap_pcd = o3d.geometry.PointCloud()
                    colmap_pcd.points = o3d.utility.Vector3dVector(colmap_points[:, :3])
                    colmap_pcd.colors = o3d.utility.Vector3dVector(colmap_points[:, 3:6])
                    colmap_pcd.paint_uniform_color([1, 0, 0])  # 红色
                    
                    # 深度点云
                    depth_pcd = self._generate_open3d_point_cloud()
                    if depth_pcd is not None:
                        depth_pcd.paint_uniform_color([0, 0, 1])  # 蓝色
                        
                        # 可视化对比
                        o3d.visualization.draw_geometries([colmap_pcd, depth_pcd],
                                                        window_name="COLMAP (Red) vs Depth (Blue)")
                        
        except Exception as e:
            self.logger.error(f"Error comparing COLMAP with depth: {e}")

def main():
    parser = argparse.ArgumentParser(description="深度分析和场景可视化工具")
    parser.add_argument("--data_dir", required=True, help="数据目录路径")
    parser.add_argument("--images_dir", required=True, help="RGB图像目录")
    parser.add_argument("--depth_dir", required=True, help="深度图目录")
    parser.add_argument("--intrinsics", required=True, help="内参文件路径")
    parser.add_argument("--extrinsics", required=True, help="外参文件路径")
    parser.add_argument("--output_dir", default="output", help="输出目录")
    
    parser.add_argument("--viz", choices=["viser", "open3d", "scenepic", "all"], 
                       default="all", help="可视化方法")
    parser.add_argument("--colmap", action="store_true", help="运行COLMAP")
    parser.add_argument("--monocular_depth", choices=["depthanything_v2", "depth_pro"], 
                       help="单目深度估计方法")
    parser.add_argument("--port", type=int, default=8080, help="Viser端口")
    
    args = parser.parse_args()
    
    # 创建分析器
    analyzer = DepthAnalyzer(args.data_dir, args.output_dir)
    
    # 加载数据
    analyzer.load_camera_data(args.images_dir, args.depth_dir, 
                             args.intrinsics, args.extrinsics)
    
    # 分析深度特征
    analyzer.analyze_depth_characteristics()
    
    # 可视化
    if args.viz in ["viser", "all"] and HAS_VISER:
        analyzer.visualize_with_viser(args.port)
    
    if args.viz in ["open3d", "all"] and HAS_OPEN3D:
        analyzer.visualize_with_open3d()
        
    if args.viz in ["scenepic", "all"] and HAS_SCENEPIC:
        analyzer.visualize_with_scenepic()
    
    # COLMAP处理
    if args.colmap:
        analyzer.run_colmap()
    
    # 单目深度估计
    if args.monocular_depth:
        analyzer.estimate_monocular_depth(args.monocular_depth)

if __name__ == "__main__":
    main()