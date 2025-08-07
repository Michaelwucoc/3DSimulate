import os
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import shutil

from models.task import Task, ReconstructionResult
from services.file_service import FileService
from utils.logger import TaskLogger, PerformanceLogger

class ReconstructionService:
    """3D重建服务类，负责调用各种重建算法"""
    
    def __init__(self, config):
        self.config = config
        self.file_service = FileService(config)
        self.performance_logger = PerformanceLogger()
        
        # 检查依赖工具
        self._check_dependencies()
    
    def _check_dependencies(self):
        """检查必要的依赖工具是否可用"""
        dependencies = {
            'colmap': self.config.TOOLS_CONFIG['colmap_path'],
            'ffmpeg': self.config.TOOLS_CONFIG['ffmpeg_path']
        }
        
        for tool, path in dependencies.items():
            if not self._is_tool_available(path):
                print(f"警告: {tool} 不可用，路径: {path}")
    
    def _is_tool_available(self, tool_path: str) -> bool:
        """检查工具是否可用"""
        try:
            result = subprocess.run(
                [tool_path, '--help'],
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            return False
    
    def process_nerf(self, task: Task) -> ReconstructionResult:
        """处理NeRF重建任务"""
        task_logger = TaskLogger(task.id)
        
        try:
            task_logger.info("开始NeRF重建任务")
            self.performance_logger.start_timer('nerf_reconstruction')
            
            # 更新任务进度
            task.progress = 5
            task.message = "准备数据..."
            
            # 步骤1: 准备数据
            task.add_step('data_preparation', '准备COLMAP数据')
            task.start_step('data_preparation')
            
            data_dir = self._prepare_nerf_data(task, task_logger)
            
            task.complete_step('data_preparation', '数据准备完成')
            task.progress = 15
            
            # 步骤2: 运行COLMAP
            task.add_step('colmap_processing', '运行COLMAP特征提取和匹配')
            task.start_step('colmap_processing')
            
            colmap_result = self._run_colmap(data_dir, task, task_logger)
            
            task.complete_step('colmap_processing', 'COLMAP处理完成')
            task.progress = 40
            
            # 步骤3: 训练NeRF模型
            task.add_step('nerf_training', '训练NeRF模型')
            task.start_step('nerf_training')
            
            model_result = self._train_nerf_model(data_dir, task, task_logger)
            
            task.complete_step('nerf_training', 'NeRF训练完成')
            task.progress = 80
            
            # 步骤4: 导出结果
            task.add_step('export_results', '导出重建结果')
            task.start_step('export_results')
            
            result = self._export_nerf_results(model_result, task, task_logger)
            
            task.complete_step('export_results', '结果导出完成')
            task.progress = 100
            
            processing_time = self.performance_logger.end_timer('nerf_reconstruction')
            task_logger.info(f"NeRF重建完成，耗时: {processing_time:.2f}秒")
            
            return result
            
        except Exception as e:
            task_logger.error(f"NeRF重建失败: {str(e)}")
            raise
        finally:
            task_logger.close()
    
    def process_3dgs(self, task: Task) -> ReconstructionResult:
        """处理3D Gaussian Splatting重建任务"""
        task_logger = TaskLogger(task.id)
        
        try:
            task_logger.info("开始3D Gaussian Splatting重建任务")
            self.performance_logger.start_timer('3dgs_reconstruction')
            
            # 更新任务进度
            task.progress = 5
            task.message = "准备数据..."
            
            # 步骤1: 准备数据
            task.add_step('data_preparation', '准备COLMAP数据')
            task.start_step('data_preparation')
            
            data_dir = self._prepare_3dgs_data(task, task_logger)
            
            task.complete_step('data_preparation', '数据准备完成')
            task.progress = 15
            
            # 步骤2: 运行COLMAP
            task.add_step('colmap_processing', '运行COLMAP特征提取和匹配')
            task.start_step('colmap_processing')
            
            colmap_result = self._run_colmap(data_dir, task, task_logger)
            
            task.complete_step('colmap_processing', 'COLMAP处理完成')
            task.progress = 40
            
            # 步骤3: 训练3DGS模型
            task.add_step('3dgs_training', '训练3D Gaussian Splatting模型')
            task.start_step('3dgs_training')
            
            model_result = self._train_3dgs_model(data_dir, task, task_logger)
            
            task.complete_step('3dgs_training', '3DGS训练完成')
            task.progress = 80
            
            # 步骤4: 导出结果
            task.add_step('export_results', '导出重建结果')
            task.start_step('export_results')
            
            result = self._export_3dgs_results(model_result, task, task_logger)
            
            task.complete_step('export_results', '结果导出完成')
            task.progress = 100
            
            processing_time = self.performance_logger.end_timer('3dgs_reconstruction')
            task_logger.info(f"3DGS重建完成，耗时: {processing_time:.2f}秒")
            
            return result
            
        except Exception as e:
            task_logger.error(f"3DGS重建失败: {str(e)}")
            raise
        finally:
            task_logger.close()
    
    def _prepare_nerf_data(self, task: Task, logger: TaskLogger) -> str:
        """为NeRF准备数据"""
        try:
            data_dir = os.path.join(task.output_folder, 'nerf_data')
            os.makedirs(data_dir, exist_ok=True)
            
            # 使用文件服务准备COLMAP数据
            prepared_dir = self.file_service.prepare_colmap_data(
                task.files, data_dir
            )
            
            logger.info(f"NeRF数据准备完成: {prepared_dir}")
            return prepared_dir
            
        except Exception as e:
            logger.error(f"NeRF数据准备失败: {str(e)}")
            raise
    
    def _prepare_3dgs_data(self, task: Task, logger: TaskLogger) -> str:
        """为3DGS准备数据"""
        try:
            data_dir = os.path.join(task.output_folder, '3dgs_data')
            os.makedirs(data_dir, exist_ok=True)
            
            # 使用文件服务准备COLMAP数据
            prepared_dir = self.file_service.prepare_colmap_data(
                task.files, data_dir
            )
            
            logger.info(f"3DGS数据准备完成: {prepared_dir}")
            return prepared_dir
            
        except Exception as e:
            logger.error(f"3DGS数据准备失败: {str(e)}")
            raise
    
    def _run_colmap(self, data_dir: str, task: Task, logger: TaskLogger) -> Dict[str, Any]:
        """运行COLMAP进行特征提取和匹配"""
        try:
            images_dir = os.path.join(data_dir, 'images')
            database_path = os.path.join(data_dir, 'database.db')
            sparse_dir = os.path.join(data_dir, 'sparse')
            os.makedirs(sparse_dir, exist_ok=True)
            
            colmap_config = self.config.get_colmap_config()
            
            # 特征提取
            logger.log_step('feature_extraction', 'started')
            task.update_step_progress('colmap_processing', 10, '特征提取中...')
            
            feature_cmd = [
                self.config.TOOLS_CONFIG['colmap_path'],
                'feature_extractor',
                '--database_path', database_path,
                '--image_path', images_dir,
                '--ImageReader.single_camera', '1',
                '--SiftExtraction.use_gpu', '1' if 'cuda' in self.config.GPU_CONFIG['device'] else '0'
            ]
            
            result = subprocess.run(
                feature_cmd,
                capture_output=True,
                text=True,
                timeout=1800  # 30分钟超时
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"COLMAP特征提取失败: {result.stderr}")
            
            logger.log_command(' '.join(feature_cmd), result.stdout, result.stderr)
            logger.log_step('feature_extraction', 'completed')
            
            # 特征匹配
            logger.log_step('feature_matching', 'started')
            task.update_step_progress('colmap_processing', 20, '特征匹配中...')
            
            matching_cmd = [
                self.config.TOOLS_CONFIG['colmap_path'],
                'exhaustive_matcher',
                '--database_path', database_path,
                '--SiftMatching.use_gpu', '1' if 'cuda' in self.config.GPU_CONFIG['device'] else '0'
            ]
            
            result = subprocess.run(
                matching_cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 1小时超时
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"COLMAP特征匹配失败: {result.stderr}")
            
            logger.log_command(' '.join(matching_cmd), result.stdout, result.stderr)
            logger.log_step('feature_matching', 'completed')
            
            # 稀疏重建
            logger.log_step('sparse_reconstruction', 'started')
            task.update_step_progress('colmap_processing', 30, '稀疏重建中...')
            
            mapper_cmd = [
                self.config.TOOLS_CONFIG['colmap_path'],
                'mapper',
                '--database_path', database_path,
                '--image_path', images_dir,
                '--output_path', sparse_dir
            ]
            
            result = subprocess.run(
                mapper_cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 1小时超时
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"COLMAP稀疏重建失败: {result.stderr}")
            
            logger.log_command(' '.join(mapper_cmd), result.stdout, result.stderr)
            logger.log_step('sparse_reconstruction', 'completed')
            
            # 检查重建结果
            reconstruction_dirs = [d for d in os.listdir(sparse_dir) 
                                 if os.path.isdir(os.path.join(sparse_dir, d))]
            
            if not reconstruction_dirs:
                raise RuntimeError("COLMAP稀疏重建没有产生结果")
            
            # 使用第一个重建结果
            reconstruction_dir = os.path.join(sparse_dir, reconstruction_dirs[0])
            
            return {
                'database_path': database_path,
                'sparse_dir': reconstruction_dir,
                'images_dir': images_dir,
                'reconstruction_count': len(reconstruction_dirs)
            }
            
        except subprocess.TimeoutExpired:
            logger.error("COLMAP处理超时")
            raise RuntimeError("COLMAP处理超时")
        except Exception as e:
            logger.error(f"COLMAP处理失败: {str(e)}")
            raise
    
    def _train_nerf_model(self, data_dir: str, task: Task, logger: TaskLogger) -> Dict[str, Any]:
        """训练NeRF模型（模拟实现）"""
        try:
            logger.info("开始训练NeRF模型")
            
            # 创建输出目录
            model_dir = os.path.join(task.output_folder, 'nerf_model')
            os.makedirs(model_dir, exist_ok=True)
            
            # 模拟训练过程
            nerf_config = self.config.get_nerf_config(task.method)
            max_iterations = nerf_config['max_num_iterations']
            
            # 模拟训练进度
            for i in range(0, max_iterations, max_iterations // 10):
                progress = int((i / max_iterations) * 100)
                task.update_step_progress('nerf_training', progress, 
                                        f'训练中... 迭代 {i}/{max_iterations}')
                time.sleep(0.1)  # 模拟训练时间
            
            # 创建模拟的模型文件
            model_files = {
                'config': os.path.join(model_dir, 'config.yml'),
                'checkpoint': os.path.join(model_dir, 'nerfacto.ckpt'),
                'metadata': os.path.join(model_dir, 'metadata.json')
            }
            
            # 创建配置文件
            config_content = f"""
method_name: {task.method}
data: {data_dir}
max_num_iterations: {max_iterations}
timestamp: {datetime.now().isoformat()}
"""
            
            with open(model_files['config'], 'w') as f:
                f.write(config_content)
            
            # 创建元数据文件
            metadata = {
                'method': task.method,
                'iterations': max_iterations,
                'data_dir': data_dir,
                'model_dir': model_dir,
                'created_at': datetime.now().isoformat(),
                'task_id': task.id
            }
            
            with open(model_files['metadata'], 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # 创建模拟的检查点文件
            with open(model_files['checkpoint'], 'w') as f:
                f.write(f"# NeRF模型检查点文件 - 任务ID: {task.id}\n")
            
            logger.info(f"NeRF模型训练完成: {model_dir}")
            
            return {
                'model_dir': model_dir,
                'model_files': model_files,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"NeRF模型训练失败: {str(e)}")
            raise
    
    def _train_3dgs_model(self, data_dir: str, task: Task, logger: TaskLogger) -> Dict[str, Any]:
        """训练3D Gaussian Splatting模型（模拟实现）"""
        try:
            logger.info("开始训练3D Gaussian Splatting模型")
            
            # 创建输出目录
            model_dir = os.path.join(task.output_folder, '3dgs_model')
            os.makedirs(model_dir, exist_ok=True)
            
            # 模拟训练过程
            gs_config = self.config.GAUSSIAN_SPLATTING_CONFIG
            max_iterations = gs_config['iterations']
            
            # 模拟训练进度
            for i in range(0, max_iterations, max_iterations // 10):
                progress = int((i / max_iterations) * 100)
                task.update_step_progress('3dgs_training', progress, 
                                        f'训练中... 迭代 {i}/{max_iterations}')
                time.sleep(0.1)  # 模拟训练时间
            
            # 创建模拟的模型文件
            model_files = {
                'point_cloud': os.path.join(model_dir, 'point_cloud.ply'),
                'config': os.path.join(model_dir, 'cfg_args'),
                'metadata': os.path.join(model_dir, 'metadata.json')
            }
            
            # 创建配置文件
            config_content = f"""
iterations: {max_iterations}
resolution: {gs_config['resolution']}
sh_degree: {gs_config['sh_degree']}
data_device: {gs_config['data_device']}
timestamp: {datetime.now().isoformat()}
"""
            
            with open(model_files['config'], 'w') as f:
                f.write(config_content)
            
            # 创建元数据文件
            metadata = {
                'method': '3dgs',
                'iterations': max_iterations,
                'data_dir': data_dir,
                'model_dir': model_dir,
                'created_at': datetime.now().isoformat(),
                'task_id': task.id
            }
            
            with open(model_files['metadata'], 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # 创建模拟的点云文件
            with open(model_files['point_cloud'], 'w') as f:
                f.write(f"# 3D Gaussian Splatting点云文件 - 任务ID: {task.id}\n")
            
            logger.info(f"3DGS模型训练完成: {model_dir}")
            
            return {
                'model_dir': model_dir,
                'model_files': model_files,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"3DGS模型训练失败: {str(e)}")
            raise
    
    def _export_nerf_results(self, model_result: Dict[str, Any], 
                           task: Task, logger: TaskLogger) -> ReconstructionResult:
        """导出NeRF重建结果"""
        try:
            logger.info("开始导出NeRF结果")
            
            export_dir = os.path.join(task.output_folder, 'exports')
            os.makedirs(export_dir, exist_ok=True)
            
            # 创建缩略图（模拟）
            thumbnail_path = os.path.join(export_dir, 'thumbnail.jpg')
            with open(thumbnail_path, 'w') as f:
                f.write(f"# NeRF缩略图 - 任务ID: {task.id}\n")
            
            # 创建导出的模型文件
            exported_model_path = os.path.join(export_dir, 'nerf_model.zip')
            with open(exported_model_path, 'w') as f:
                f.write(f"# NeRF导出模型 - 任务ID: {task.id}\n")
            
            result = ReconstructionResult(
                model_path=exported_model_path,
                thumbnail_path=thumbnail_path,
                metadata_path=model_result['model_files']['metadata'],
                num_points=50000,  # 模拟数据
                model_size_mb=15.5,
                psnr=28.5,
                ssim=0.85,
                export_formats=['ply', 'obj']
            )
            
            logger.info("NeRF结果导出完成")
            return result
            
        except Exception as e:
            logger.error(f"NeRF结果导出失败: {str(e)}")
            raise
    
    def _export_3dgs_results(self, model_result: Dict[str, Any], 
                           task: Task, logger: TaskLogger) -> ReconstructionResult:
        """导出3DGS重建结果"""
        try:
            logger.info("开始导出3DGS结果")
            
            export_dir = os.path.join(task.output_folder, 'exports')
            os.makedirs(export_dir, exist_ok=True)
            
            # 创建缩略图（模拟）
            thumbnail_path = os.path.join(export_dir, 'thumbnail.jpg')
            with open(thumbnail_path, 'w') as f:
                f.write(f"# 3DGS缩略图 - 任务ID: {task.id}\n")
            
            # 复制点云文件
            point_cloud_path = os.path.join(export_dir, 'point_cloud.ply')
            shutil.copy2(model_result['model_files']['point_cloud'], point_cloud_path)
            
            result = ReconstructionResult(
                model_path=point_cloud_path,
                thumbnail_path=thumbnail_path,
                metadata_path=model_result['model_files']['metadata'],
                point_cloud_path=point_cloud_path,
                num_points=100000,  # 模拟数据
                model_size_mb=25.8,
                psnr=30.2,
                ssim=0.88,
                export_formats=['ply', 'obj', 'gltf']
            )
            
            logger.info("3DGS结果导出完成")
            return result
            
        except Exception as e:
            logger.error(f"3DGS结果导出失败: {str(e)}")
            raise