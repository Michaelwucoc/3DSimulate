import os
import shutil
import mimetypes
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import hashlib
import subprocess
from PIL import Image
import cv2
import json
from datetime import datetime

from models.task import UploadedFile
from utils.logger import get_logger

class FileService:
    """文件服务类，处理文件上传、验证、转换等操作"""
    
    def __init__(self, config):
        self.config = config
        self.logger = get_logger('file_service')
        
        # 支持的文件类型
        self.SUPPORTED_VIDEO_FORMATS = {
            '.mp4', '.avi', '.mov', '.mkv', '.webm', '.m4v', '.flv', '.wmv'
        }
        
        self.SUPPORTED_IMAGE_FORMATS = {
            '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp'
        }
        
        # 确保目录存在
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            self.config.UPLOAD_FOLDER,
            self.config.OUTPUT_FOLDER,
            self.config.TEMP_FOLDER
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def validate_file(self, file_path: str) -> Tuple[bool, str]:
        """验证文件是否有效
        
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        try:
            if not os.path.exists(file_path):
                return False, "文件不存在"
            
            # 检查文件大小
            file_size = os.path.getsize(file_path)
            if file_size > self.config.MAX_FILE_SIZE:
                return False, f"文件大小超过限制 ({self.config.MAX_FILE_SIZE / 1024 / 1024:.1f}MB)"
            
            if file_size == 0:
                return False, "文件为空"
            
            # 检查文件扩展名
            file_ext = Path(file_path).suffix.lower()
            if file_ext not in self.SUPPORTED_VIDEO_FORMATS and file_ext not in self.SUPPORTED_IMAGE_FORMATS:
                return False, f"不支持的文件格式: {file_ext}"
            
            # 验证文件内容
            if file_ext in self.SUPPORTED_VIDEO_FORMATS:
                return self._validate_video_file(file_path)
            elif file_ext in self.SUPPORTED_IMAGE_FORMATS:
                return self._validate_image_file(file_path)
            
            return True, ""
            
        except Exception as e:
            self.logger.error(f"文件验证失败: {str(e)}")
            return False, f"文件验证失败: {str(e)}"
    
    def _validate_video_file(self, file_path: str) -> Tuple[bool, str]:
        """验证视频文件"""
        try:
            # 使用OpenCV验证视频文件
            cap = cv2.VideoCapture(file_path)
            if not cap.isOpened():
                return False, "无法打开视频文件"
            
            # 检查视频属性
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            cap.release()
            
            if frame_count < 10:
                return False, "视频帧数太少（至少需要10帧）"
            
            if fps < 1 or fps > 120:
                return False, f"视频帧率异常: {fps}"
            
            if width < 100 or height < 100:
                return False, f"视频分辨率太低: {width}x{height}"
            
            if width > 4096 or height > 4096:
                return False, f"视频分辨率太高: {width}x{height}"
            
            return True, ""
            
        except Exception as e:
            return False, f"视频文件验证失败: {str(e)}"
    
    def _validate_image_file(self, file_path: str) -> Tuple[bool, str]:
        """验证图像文件"""
        try:
            # 使用PIL验证图像文件
            with Image.open(file_path) as img:
                width, height = img.size
                
                if width < 100 or height < 100:
                    return False, f"图像分辨率太低: {width}x{height}"
                
                if width > 4096 or height > 4096:
                    return False, f"图像分辨率太高: {width}x{height}"
                
                # 检查图像模式
                if img.mode not in ['RGB', 'RGBA', 'L']:
                    return False, f"不支持的图像模式: {img.mode}"
            
            return True, ""
            
        except Exception as e:
            return False, f"图像文件验证失败: {str(e)}"
    
    def get_file_info(self, file_path: str) -> Dict:
        """获取文件详细信息"""
        try:
            file_path = Path(file_path)
            stat = file_path.stat()
            
            info = {
                'name': file_path.name,
                'size': stat.st_size,
                'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'extension': file_path.suffix.lower(),
                'mime_type': mimetypes.guess_type(str(file_path))[0]
            }
            
            # 计算文件哈希
            info['md5'] = self._calculate_file_hash(str(file_path))
            
            # 根据文件类型获取额外信息
            if info['extension'] in self.SUPPORTED_VIDEO_FORMATS:
                info.update(self._get_video_info(str(file_path)))
            elif info['extension'] in self.SUPPORTED_IMAGE_FORMATS:
                info.update(self._get_image_info(str(file_path)))
            
            return info
            
        except Exception as e:
            self.logger.error(f"获取文件信息失败: {str(e)}")
            return {}
    
    def _get_video_info(self, file_path: str) -> Dict:
        """获取视频文件信息"""
        try:
            cap = cv2.VideoCapture(file_path)
            if not cap.isOpened():
                return {}
            
            info = {
                'type': 'video',
                'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                'fps': cap.get(cv2.CAP_PROP_FPS),
                'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'duration': cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS)
            }
            
            cap.release()
            return info
            
        except Exception as e:
            self.logger.error(f"获取视频信息失败: {str(e)}")
            return {'type': 'video'}
    
    def _get_image_info(self, file_path: str) -> Dict:
        """获取图像文件信息"""
        try:
            with Image.open(file_path) as img:
                return {
                    'type': 'image',
                    'width': img.width,
                    'height': img.height,
                    'mode': img.mode,
                    'format': img.format
                }
        except Exception as e:
            self.logger.error(f"获取图像信息失败: {str(e)}")
            return {'type': 'image'}
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """计算文件MD5哈希值"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            self.logger.error(f"计算文件哈希失败: {str(e)}")
            return ""
    
    def extract_video_frames(self, video_path: str, output_dir: str, 
                           max_frames: int = 100, quality: str = 'medium') -> List[str]:
        """从视频中提取帧
        
        Args:
            video_path: 视频文件路径
            output_dir: 输出目录
            max_frames: 最大帧数
            quality: 质量设置 ('low', 'medium', 'high')
        
        Returns:
            List[str]: 提取的帧文件路径列表
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError("无法打开视频文件")
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            # 计算帧间隔
            if total_frames <= max_frames:
                frame_interval = 1
            else:
                frame_interval = total_frames // max_frames
            
            # 设置质量参数
            quality_settings = {
                'low': {'scale': 0.5, 'jpeg_quality': 70},
                'medium': {'scale': 0.75, 'jpeg_quality': 85},
                'high': {'scale': 1.0, 'jpeg_quality': 95}
            }
            
            settings = quality_settings.get(quality, quality_settings['medium'])
            
            extracted_frames = []
            frame_count = 0
            saved_count = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_count % frame_interval == 0 and saved_count < max_frames:
                    # 调整图像大小
                    if settings['scale'] != 1.0:
                        height, width = frame.shape[:2]
                        new_width = int(width * settings['scale'])
                        new_height = int(height * settings['scale'])
                        frame = cv2.resize(frame, (new_width, new_height))
                    
                    # 保存帧
                    frame_filename = f"frame_{saved_count:06d}.jpg"
                    frame_path = os.path.join(output_dir, frame_filename)
                    
                    cv2.imwrite(frame_path, frame, 
                              [cv2.IMWRITE_JPEG_QUALITY, settings['jpeg_quality']])
                    
                    extracted_frames.append(frame_path)
                    saved_count += 1
                
                frame_count += 1
            
            cap.release()
            
            self.logger.info(f"从视频中提取了 {len(extracted_frames)} 帧")
            return extracted_frames
            
        except Exception as e:
            self.logger.error(f"提取视频帧失败: {str(e)}")
            raise
    
    def prepare_colmap_data(self, input_files: List[UploadedFile], output_dir: str) -> str:
        """为COLMAP准备数据
        
        Args:
            input_files: 输入文件列表
            output_dir: 输出目录
        
        Returns:
            str: 准备好的数据目录路径
        """
        try:
            # 创建COLMAP数据结构
            images_dir = os.path.join(output_dir, 'images')
            os.makedirs(images_dir, exist_ok=True)
            
            processed_files = []
            
            for file_info in input_files:
                file_path = file_info.path
                file_ext = Path(file_path).suffix.lower()
                
                if file_ext in self.SUPPORTED_VIDEO_FORMATS:
                    # 从视频提取帧
                    video_frames_dir = os.path.join(output_dir, f'frames_{file_info.id}')
                    frames = self.extract_video_frames(file_path, video_frames_dir)
                    
                    # 复制帧到images目录
                    for i, frame_path in enumerate(frames):
                        dest_name = f"{file_info.id}_frame_{i:06d}.jpg"
                        dest_path = os.path.join(images_dir, dest_name)
                        shutil.copy2(frame_path, dest_path)
                        processed_files.append(dest_path)
                
                elif file_ext in self.SUPPORTED_IMAGE_FORMATS:
                    # 直接复制图像文件
                    dest_name = f"{file_info.id}_{Path(file_path).name}"
                    dest_path = os.path.join(images_dir, dest_name)
                    shutil.copy2(file_path, dest_path)
                    processed_files.append(dest_path)
            
            # 创建数据集信息文件
            dataset_info = {
                'images_dir': images_dir,
                'num_images': len(processed_files),
                'source_files': [f.to_dict() for f in input_files],
                'created_at': datetime.now().isoformat()
            }
            
            info_path = os.path.join(output_dir, 'dataset_info.json')
            with open(info_path, 'w', encoding='utf-8') as f:
                json.dump(dataset_info, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"为COLMAP准备了 {len(processed_files)} 张图像")
            return output_dir
            
        except Exception as e:
            self.logger.error(f"准备COLMAP数据失败: {str(e)}")
            raise
    
    def cleanup_temp_files(self, directory: str, max_age_hours: int = 24):
        """清理临时文件
        
        Args:
            directory: 要清理的目录
            max_age_hours: 文件最大保留时间（小时）
        """
        try:
            if not os.path.exists(directory):
                return
            
            current_time = datetime.now().timestamp()
            max_age_seconds = max_age_hours * 3600
            
            cleaned_count = 0
            
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        file_age = current_time - os.path.getmtime(file_path)
                        if file_age > max_age_seconds:
                            os.remove(file_path)
                            cleaned_count += 1
                    except OSError:
                        continue
                
                # 删除空目录
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    try:
                        if not os.listdir(dir_path):
                            os.rmdir(dir_path)
                    except OSError:
                        continue
            
            if cleaned_count > 0:
                self.logger.info(f"清理了 {cleaned_count} 个临时文件")
                
        except Exception as e:
            self.logger.error(f"清理临时文件失败: {str(e)}")
    
    def get_storage_usage(self) -> Dict[str, int]:
        """获取存储使用情况"""
        try:
            def get_dir_size(directory):
                total_size = 0
                if os.path.exists(directory):
                    for dirpath, dirnames, filenames in os.walk(directory):
                        for filename in filenames:
                            filepath = os.path.join(dirpath, filename)
                            try:
                                total_size += os.path.getsize(filepath)
                            except OSError:
                                continue
                return total_size
            
            return {
                'uploads': get_dir_size(self.config.UPLOAD_FOLDER),
                'outputs': get_dir_size(self.config.OUTPUT_FOLDER),
                'temp': get_dir_size(self.config.TEMP_FOLDER),
                'total': get_dir_size(self.config.UPLOAD_FOLDER) + 
                        get_dir_size(self.config.OUTPUT_FOLDER) + 
                        get_dir_size(self.config.TEMP_FOLDER)
            }
            
        except Exception as e:
            self.logger.error(f"获取存储使用情况失败: {str(e)}")
            return {'uploads': 0, 'outputs': 0, 'temp': 0, 'total': 0}