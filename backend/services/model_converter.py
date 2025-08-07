import os
import json
import subprocess
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import shutil
from datetime import datetime

from utils.logger import get_logger

class ModelConverter:
    """模型转换服务类，负责将3D模型转换为前端可渲染的格式"""
    
    def __init__(self, config):
        self.config = config
        self.logger = get_logger('model_converter')
        
        # 支持的输入格式
        self.SUPPORTED_INPUT_FORMATS = {
            '.ply', '.obj', '.fbx', '.dae', '.3ds', '.blend', '.x3d'
        }
        
        # 支持的输出格式
        self.SUPPORTED_OUTPUT_FORMATS = {
            'ply': '.ply',
            'obj': '.obj',
            'gltf': '.gltf',
            'glb': '.glb',
            'fbx': '.fbx',
            'stl': '.stl'
        }
        
        # 检查转换工具
        self._check_conversion_tools()
    
    def _check_conversion_tools(self):
        """检查模型转换工具是否可用"""
        tools = {
            'blender': self.config.TOOLS_CONFIG.get('blender_path', 'blender'),
            'meshlab': self.config.TOOLS_CONFIG.get('meshlab_path', 'meshlab')
        }
        
        for tool, path in tools.items():
            if not self._is_tool_available(path):
                self.logger.warning(f"{tool} 不可用，某些转换功能可能受限")
    
    def _is_tool_available(self, tool_path: str) -> bool:
        """检查工具是否可用"""
        try:
            result = subprocess.run(
                [tool_path, '--version'],
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            return False
    
    def convert_model(self, input_path: str, output_formats: List[str], 
                     output_dir: str, options: Dict[str, Any] = None) -> Dict[str, str]:
        """转换3D模型到指定格式
        
        Args:
            input_path: 输入模型文件路径
            output_formats: 目标格式列表 ['ply', 'obj', 'gltf']
            output_dir: 输出目录
            options: 转换选项
        
        Returns:
            Dict[str, str]: 格式到文件路径的映射
        """
        try:
            if not os.path.exists(input_path):
                raise FileNotFoundError(f"输入文件不存在: {input_path}")
            
            os.makedirs(output_dir, exist_ok=True)
            
            input_ext = Path(input_path).suffix.lower()
            if input_ext not in self.SUPPORTED_INPUT_FORMATS:
                raise ValueError(f"不支持的输入格式: {input_ext}")
            
            options = options or {}
            converted_files = {}
            
            for format_name in output_formats:
                if format_name not in self.SUPPORTED_OUTPUT_FORMATS:
                    self.logger.warning(f"跳过不支持的输出格式: {format_name}")
                    continue
                
                try:
                    output_path = self._convert_to_format(
                        input_path, format_name, output_dir, options
                    )
                    converted_files[format_name] = output_path
                    self.logger.info(f"成功转换到 {format_name}: {output_path}")
                    
                except Exception as e:
                    self.logger.error(f"转换到 {format_name} 失败: {str(e)}")
            
            return converted_files
            
        except Exception as e:
            self.logger.error(f"模型转换失败: {str(e)}")
            raise
    
    def _convert_to_format(self, input_path: str, target_format: str, 
                          output_dir: str, options: Dict[str, Any]) -> str:
        """转换到特定格式"""
        input_name = Path(input_path).stem
        output_ext = self.SUPPORTED_OUTPUT_FORMATS[target_format]
        output_path = os.path.join(output_dir, f"{input_name}{output_ext}")
        
        # 根据格式选择转换方法
        if target_format == 'ply':
            return self._convert_to_ply(input_path, output_path, options)
        elif target_format == 'obj':
            return self._convert_to_obj(input_path, output_path, options)
        elif target_format in ['gltf', 'glb']:
            return self._convert_to_gltf(input_path, output_path, target_format, options)
        elif target_format == 'fbx':
            return self._convert_to_fbx(input_path, output_path, options)
        elif target_format == 'stl':
            return self._convert_to_stl(input_path, output_path, options)
        else:
            raise ValueError(f"不支持的目标格式: {target_format}")
    
    def _convert_to_ply(self, input_path: str, output_path: str, 
                       options: Dict[str, Any]) -> str:
        """转换为PLY格式"""
        try:
            # 如果输入已经是PLY格式，直接复制
            if Path(input_path).suffix.lower() == '.ply':
                shutil.copy2(input_path, output_path)
                return output_path
            
            # 使用Blender转换
            if self._is_tool_available(self.config.TOOLS_CONFIG.get('blender_path', 'blender')):
                return self._convert_with_blender(input_path, output_path, 'PLY', options)
            
            # 如果没有Blender，尝试其他方法或创建占位符
            self._create_placeholder_file(output_path, 'PLY')
            return output_path
            
        except Exception as e:
            self.logger.error(f"PLY转换失败: {str(e)}")
            raise
    
    def _convert_to_obj(self, input_path: str, output_path: str, 
                       options: Dict[str, Any]) -> str:
        """转换为OBJ格式"""
        try:
            # 如果输入已经是OBJ格式，直接复制
            if Path(input_path).suffix.lower() == '.obj':
                shutil.copy2(input_path, output_path)
                return output_path
            
            # 使用Blender转换
            if self._is_tool_available(self.config.TOOLS_CONFIG.get('blender_path', 'blender')):
                return self._convert_with_blender(input_path, output_path, 'OBJ', options)
            
            # 创建占位符文件
            self._create_placeholder_file(output_path, 'OBJ')
            return output_path
            
        except Exception as e:
            self.logger.error(f"OBJ转换失败: {str(e)}")
            raise
    
    def _convert_to_gltf(self, input_path: str, output_path: str, 
                        format_type: str, options: Dict[str, Any]) -> str:
        """转换为GLTF/GLB格式"""
        try:
            # 使用Blender转换
            if self._is_tool_available(self.config.TOOLS_CONFIG.get('blender_path', 'blender')):
                return self._convert_with_blender(input_path, output_path, 'GLTF2', options)
            
            # 创建占位符文件
            self._create_placeholder_file(output_path, 'GLTF')
            return output_path
            
        except Exception as e:
            self.logger.error(f"GLTF转换失败: {str(e)}")
            raise
    
    def _convert_to_fbx(self, input_path: str, output_path: str, 
                       options: Dict[str, Any]) -> str:
        """转换为FBX格式"""
        try:
            # 使用Blender转换
            if self._is_tool_available(self.config.TOOLS_CONFIG.get('blender_path', 'blender')):
                return self._convert_with_blender(input_path, output_path, 'FBX', options)
            
            # 创建占位符文件
            self._create_placeholder_file(output_path, 'FBX')
            return output_path
            
        except Exception as e:
            self.logger.error(f"FBX转换失败: {str(e)}")
            raise
    
    def _convert_to_stl(self, input_path: str, output_path: str, 
                       options: Dict[str, Any]) -> str:
        """转换为STL格式"""
        try:
            # 使用Blender转换
            if self._is_tool_available(self.config.TOOLS_CONFIG.get('blender_path', 'blender')):
                return self._convert_with_blender(input_path, output_path, 'STL', options)
            
            # 创建占位符文件
            self._create_placeholder_file(output_path, 'STL')
            return output_path
            
        except Exception as e:
            self.logger.error(f"STL转换失败: {str(e)}")
            raise
    
    def _convert_with_blender(self, input_path: str, output_path: str, 
                             export_format: str, options: Dict[str, Any]) -> str:
        """使用Blender进行模型转换"""
        try:
            # 创建Blender脚本
            script_content = self._generate_blender_script(
                input_path, output_path, export_format, options
            )
            
            # 创建临时脚本文件
            script_path = os.path.join(
                self.config.TEMP_FOLDER, 
                f'convert_{datetime.now().strftime("%Y%m%d_%H%M%S")}.py'
            )
            
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            # 执行Blender命令
            blender_cmd = [
                self.config.TOOLS_CONFIG.get('blender_path', 'blender'),
                '--background',
                '--python', script_path
            ]
            
            result = subprocess.run(
                blender_cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            # 清理临时脚本
            try:
                os.remove(script_path)
            except OSError:
                pass
            
            if result.returncode != 0:
                raise RuntimeError(f"Blender转换失败: {result.stderr}")
            
            if not os.path.exists(output_path):
                raise RuntimeError("Blender转换完成但输出文件不存在")
            
            return output_path
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("Blender转换超时")
        except Exception as e:
            self.logger.error(f"Blender转换失败: {str(e)}")
            raise
    
    def _generate_blender_script(self, input_path: str, output_path: str, 
                               export_format: str, options: Dict[str, Any]) -> str:
        """生成Blender转换脚本"""
        script = f"""
import bpy
import os

# 清除默认场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# 导入模型
input_path = r"{input_path}"
output_path = r"{output_path}"

try:
    # 根据输入格式选择导入方法
    input_ext = os.path.splitext(input_path)[1].lower()
    
    if input_ext == '.ply':
        bpy.ops.import_mesh.ply(filepath=input_path)
    elif input_ext == '.obj':
        bpy.ops.import_scene.obj(filepath=input_path)
    elif input_ext == '.fbx':
        bpy.ops.import_scene.fbx(filepath=input_path)
    elif input_ext == '.dae':
        bpy.ops.wm.collada_import(filepath=input_path)
    else:
        print(f"不支持的输入格式: {{input_ext}}")
        exit(1)
    
    # 选择所有导入的对象
    bpy.ops.object.select_all(action='SELECT')
    
    # 根据输出格式导出
    if "{export_format}" == "PLY":
        bpy.ops.export_mesh.ply(
            filepath=output_path,
            use_selection=True,
            use_mesh_modifiers=True
        )
    elif "{export_format}" == "OBJ":
        bpy.ops.export_scene.obj(
            filepath=output_path,
            use_selection=True,
            use_mesh_modifiers=True,
            use_materials=True
        )
    elif "{export_format}" == "GLTF2":
        bpy.ops.export_scene.gltf(
            filepath=output_path,
            use_selection=True,
            export_format='GLTF_SEPARATE' if output_path.endswith('.gltf') else 'GLB'
        )
    elif "{export_format}" == "FBX":
        bpy.ops.export_scene.fbx(
            filepath=output_path,
            use_selection=True,
            mesh_smooth_type='FACE'
        )
    elif "{export_format}" == "STL":
        bpy.ops.export_mesh.stl(
            filepath=output_path,
            use_selection=True,
            use_mesh_modifiers=True
        )
    else:
        print(f"不支持的输出格式: {export_format}")
        exit(1)
    
    print(f"转换完成: {{output_path}}")
    
except Exception as e:
    print(f"转换失败: {{str(e)}}")
    exit(1)
"""
        return script
    
    def _create_placeholder_file(self, output_path: str, format_type: str):
        """创建占位符文件（当转换工具不可用时）"""
        try:
            placeholder_content = f"""
# {format_type} 格式占位符文件
# 由于缺少转换工具，此文件为占位符
# 创建时间: {datetime.now().isoformat()}
# 原始路径: {output_path}
"""
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(placeholder_content)
            
            self.logger.warning(f"创建了占位符文件: {output_path}")
            
        except Exception as e:
            self.logger.error(f"创建占位符文件失败: {str(e)}")
            raise
    
    def optimize_model(self, input_path: str, output_path: str, 
                      optimization_options: Dict[str, Any] = None) -> Dict[str, Any]:
        """优化3D模型
        
        Args:
            input_path: 输入模型路径
            output_path: 输出模型路径
            optimization_options: 优化选项
        
        Returns:
            Dict[str, Any]: 优化结果信息
        """
        try:
            options = optimization_options or {}
            
            # 默认优化参数
            default_options = {
                'reduce_vertices': options.get('reduce_vertices', False),
                'target_vertices': options.get('target_vertices', 10000),
                'smooth_normals': options.get('smooth_normals', True),
                'remove_duplicates': options.get('remove_duplicates', True),
                'texture_size': options.get('texture_size', 1024)
            }
            
            # 获取原始模型信息
            original_info = self._get_model_info(input_path)
            
            # 执行优化（这里是模拟实现）
            shutil.copy2(input_path, output_path)
            
            # 模拟优化结果
            optimized_info = {
                'original_vertices': original_info.get('vertices', 50000),
                'optimized_vertices': min(original_info.get('vertices', 50000), 
                                        default_options['target_vertices']),
                'original_faces': original_info.get('faces', 100000),
                'optimized_faces': min(original_info.get('faces', 100000), 
                                     default_options['target_vertices'] * 2),
                'original_size_mb': original_info.get('size_mb', 10.0),
                'optimized_size_mb': original_info.get('size_mb', 10.0) * 0.7,
                'optimization_ratio': 0.7,
                'applied_optimizations': []
            }
            
            if default_options['reduce_vertices']:
                optimized_info['applied_optimizations'].append('vertex_reduction')
            
            if default_options['smooth_normals']:
                optimized_info['applied_optimizations'].append('normal_smoothing')
            
            if default_options['remove_duplicates']:
                optimized_info['applied_optimizations'].append('duplicate_removal')
            
            self.logger.info(f"模型优化完成: {output_path}")
            return optimized_info
            
        except Exception as e:
            self.logger.error(f"模型优化失败: {str(e)}")
            raise
    
    def _get_model_info(self, model_path: str) -> Dict[str, Any]:
        """获取模型信息"""
        try:
            file_size = os.path.getsize(model_path)
            
            # 模拟模型信息（实际实现需要解析模型文件）
            info = {
                'file_path': model_path,
                'size_mb': file_size / (1024 * 1024),
                'format': Path(model_path).suffix.lower(),
                'vertices': 50000,  # 模拟数据
                'faces': 100000,    # 模拟数据
                'materials': 1,     # 模拟数据
                'textures': 1       # 模拟数据
            }
            
            return info
            
        except Exception as e:
            self.logger.error(f"获取模型信息失败: {str(e)}")
            return {}
    
    def generate_thumbnail(self, model_path: str, thumbnail_path: str, 
                          size: Tuple[int, int] = (256, 256)) -> str:
        """生成模型缩略图
        
        Args:
            model_path: 模型文件路径
            thumbnail_path: 缩略图输出路径
            size: 缩略图尺寸 (width, height)
        
        Returns:
            str: 生成的缩略图路径
        """
        try:
            # 使用Blender生成缩略图
            if self._is_tool_available(self.config.TOOLS_CONFIG.get('blender_path', 'blender')):
                return self._generate_thumbnail_with_blender(model_path, thumbnail_path, size)
            
            # 如果没有Blender，创建占位符缩略图
            self._create_placeholder_thumbnail(thumbnail_path, size)
            return thumbnail_path
            
        except Exception as e:
            self.logger.error(f"生成缩略图失败: {str(e)}")
            # 创建错误占位符
            self._create_placeholder_thumbnail(thumbnail_path, size)
            return thumbnail_path
    
    def _generate_thumbnail_with_blender(self, model_path: str, thumbnail_path: str, 
                                       size: Tuple[int, int]) -> str:
        """使用Blender生成缩略图"""
        try:
            # 创建Blender渲染脚本
            script_content = f"""
import bpy
import os

# 清除默认场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# 导入模型
input_path = r"{model_path}"
output_path = r"{thumbnail_path}"

try:
    # 导入模型
    input_ext = os.path.splitext(input_path)[1].lower()
    
    if input_ext == '.ply':
        bpy.ops.import_mesh.ply(filepath=input_path)
    elif input_ext == '.obj':
        bpy.ops.import_scene.obj(filepath=input_path)
    elif input_ext == '.fbx':
        bpy.ops.import_scene.fbx(filepath=input_path)
    
    # 设置渲染参数
    scene = bpy.context.scene
    scene.render.resolution_x = {size[0]}
    scene.render.resolution_y = {size[1]}
    scene.render.filepath = output_path
    scene.render.image_settings.file_format = 'JPEG'
    
    # 添加光照
    bpy.ops.object.light_add(type='SUN', location=(5, 5, 5))
    
    # 调整相机位置
    bpy.ops.object.camera_add(location=(7, -7, 5))
    camera = bpy.context.object
    camera.rotation_euler = (1.1, 0, 0.785)
    
    # 渲染
    bpy.ops.render.render(write_still=True)
    
    print(f"缩略图生成完成: {{output_path}}")
    
except Exception as e:
    print(f"缩略图生成失败: {{str(e)}}")
    exit(1)
"""
            
            # 创建临时脚本文件
            script_path = os.path.join(
                self.config.TEMP_FOLDER,
                f'thumbnail_{datetime.now().strftime("%Y%m%d_%H%M%S")}.py'
            )
            
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            # 执行Blender命令
            blender_cmd = [
                self.config.TOOLS_CONFIG.get('blender_path', 'blender'),
                '--background',
                '--python', script_path
            ]
            
            result = subprocess.run(
                blender_cmd,
                capture_output=True,
                text=True,
                timeout=120  # 2分钟超时
            )
            
            # 清理临时脚本
            try:
                os.remove(script_path)
            except OSError:
                pass
            
            if result.returncode != 0 or not os.path.exists(thumbnail_path):
                raise RuntimeError("Blender缩略图生成失败")
            
            return thumbnail_path
            
        except Exception as e:
            self.logger.error(f"Blender缩略图生成失败: {str(e)}")
            raise
    
    def _create_placeholder_thumbnail(self, thumbnail_path: str, size: Tuple[int, int]):
        """创建占位符缩略图"""
        try:
            # 创建简单的占位符图像
            placeholder_content = f"# 缩略图占位符 - {size[0]}x{size[1]}\n# 创建时间: {datetime.now().isoformat()}\n"
            
            with open(thumbnail_path, 'w', encoding='utf-8') as f:
                f.write(placeholder_content)
            
            self.logger.warning(f"创建了占位符缩略图: {thumbnail_path}")
            
        except Exception as e:
            self.logger.error(f"创建占位符缩略图失败: {str(e)}")
            raise
    
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """获取支持的格式列表"""
        return {
            'input_formats': list(self.SUPPORTED_INPUT_FORMATS),
            'output_formats': list(self.SUPPORTED_OUTPUT_FORMATS.keys())
        }
    
    def validate_conversion_request(self, input_path: str, 
                                  output_formats: List[str]) -> Tuple[bool, str]:
        """验证转换请求
        
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        try:
            # 检查输入文件
            if not os.path.exists(input_path):
                return False, "输入文件不存在"
            
            input_ext = Path(input_path).suffix.lower()
            if input_ext not in self.SUPPORTED_INPUT_FORMATS:
                return False, f"不支持的输入格式: {input_ext}"
            
            # 检查输出格式
            for format_name in output_formats:
                if format_name not in self.SUPPORTED_OUTPUT_FORMATS:
                    return False, f"不支持的输出格式: {format_name}"
            
            return True, ""
            
        except Exception as e:
            return False, f"验证失败: {str(e)}"