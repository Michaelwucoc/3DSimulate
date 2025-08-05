import os
import shutil
import uuid
from pathlib import Path
from typing import List, Optional
from fastapi import UploadFile, HTTPException
from app.core.config import settings
import aiofiles

# 尝试导入magic库，如果失败则使用备用方案
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    print("Warning: python-magic not available, using fallback file type detection")

from PIL import Image
import cv2
import io

class FileStorageService:
    def __init__(self):
        self.upload_dir = Path(settings.upload_dir)
        self.models_dir = Path(settings.models_dir)
        self.temp_dir = Path("temp")
        
        # 确保目录存在
        self.upload_dir.mkdir(exist_ok=True)
        self.models_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)
    
    def _get_file_type(self, mime_type: str) -> str:
        """根据MIME类型确定文件类型"""
        if mime_type.startswith('video/'):
            return 'video'
        elif mime_type.startswith('image/'):
            return 'image'
        else:
            raise ValueError(f"不支持的文件类型: {mime_type}")
    
    def _validate_file(self, file: UploadFile) -> None:
        """验证文件"""
        # 检查文件大小
        if file.size and file.size > settings.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"文件太大，最大允许 {settings.max_file_size / (1024*1024)}MB"
            )
        
        # 检查文件类型
        if file.content_type not in settings.allowed_file_types:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {file.content_type}"
            )
    
    async def save_uploaded_file(self, file: UploadFile, user_id: str) -> dict:
        """保存上传的文件"""
        self._validate_file(file)
        
        # 生成唯一文件名
        file_id = str(uuid.uuid4())
        file_extension = Path(file.filename).suffix
        filename = f"{file_id}{file_extension}"
        
        # 创建用户目录
        user_dir = self.upload_dir / user_id
        user_dir.mkdir(exist_ok=True)
        
        file_path = user_dir / filename
        
        # 保存文件
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")
        
        # 获取文件大小
        file_size = os.path.getsize(file_path)
        
        # 验证实际文件类型
        mime_type = file.content_type
        if MAGIC_AVAILABLE:
            try:
                mime_type = magic.from_file(str(file_path), mime=True)
                if mime_type not in settings.allowed_file_types:
                    os.remove(file_path)
                    raise HTTPException(
                        status_code=400,
                        detail=f"文件类型验证失败: {mime_type}"
                    )
            except Exception as e:
                # 如果magic库不可用，使用上传时的content_type
                mime_type = file.content_type
        
        return {
            "id": file_id,
            "filename": filename,
            "original_filename": file.filename,
            "file_path": str(file_path),
            "file_size": file_size,
            "file_type": self._get_file_type(mime_type),
            "mime_type": mime_type
        }
    
    async def save_multiple_files(self, files: List[UploadFile], user_id: str) -> List[dict]:
        """保存多个文件"""
        saved_files = []
        
        for file in files:
            try:
                saved_file = await self.save_uploaded_file(file, user_id)
                saved_files.append(saved_file)
            except Exception as e:
                # 如果某个文件保存失败，删除已保存的文件
                for saved_file in saved_files:
                    try:
                        os.remove(saved_file["file_path"])
                    except:
                        pass
                raise e
        
        return saved_files
    
    def get_file_path(self, file_id: str, user_id: str) -> Optional[Path]:
        """获取文件路径"""
        user_dir = self.upload_dir / user_id
        for file_path in user_dir.glob(f"{file_id}.*"):
            return file_path
        return None
    
    def delete_file(self, file_id: str, user_id: str) -> bool:
        """删除文件"""
        file_path = self.get_file_path(file_id, user_id)
        if file_path and file_path.exists():
            try:
                os.remove(file_path)
                return True
            except:
                return False
        return False
    
    def save_model_file(self, model_data: bytes, task_id: str, format: str = "glb") -> str:
        """保存3D模型文件"""
        model_filename = f"{task_id}.{format}"
        model_path = self.models_dir / model_filename
        
        try:
            with open(model_path, 'wb') as f:
                f.write(model_data)
            return str(model_path)
        except Exception as e:
            raise Exception(f"模型文件保存失败: {str(e)}")
    
    def save_thumbnail(self, image_data: bytes, task_id: str) -> str:
        """保存缩略图"""
        thumbnail_filename = f"{task_id}_thumb.jpg"
        thumbnail_path = self.models_dir / thumbnail_filename
        
        try:
            # 使用PIL处理图片
            image = Image.open(io.BytesIO(image_data))
            image.thumbnail((400, 400))  # 缩放到400x400
            image.save(thumbnail_path, "JPEG", quality=85)
            return str(thumbnail_path)
        except Exception as e:
            raise Exception(f"缩略图保存失败: {str(e)}")
    
    def extract_frames_from_video(self, video_path: str, output_dir: str, frame_rate: int = 1) -> List[str]:
        """从视频中提取帧"""
        frames = []
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise Exception("无法打开视频文件")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(fps / frame_rate)
        frame_count = 0
        saved_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % frame_interval == 0:
                frame_filename = f"frame_{saved_count:04d}.jpg"
                frame_path = os.path.join(output_dir, frame_filename)
                cv2.imwrite(frame_path, frame)
                frames.append(frame_path)
                saved_count += 1
            
            frame_count += 1
        
        cap.release()
        return frames
    
    def cleanup_temp_files(self, temp_dir: str) -> None:
        """清理临时文件"""
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"清理临时文件失败: {str(e)}")
    
    def get_storage_info(self) -> dict:
        """获取存储信息"""
        total_size = 0
        file_count = 0
        
        for root, dirs, files in os.walk(self.upload_dir):
            for file in files:
                file_path = os.path.join(root, file)
                total_size += os.path.getsize(file_path)
                file_count += 1
        
        return {
            "total_size": total_size,
            "file_count": file_count,
            "upload_dir": str(self.upload_dir),
            "models_dir": str(self.models_dir)
        }

# 创建全局文件存储服务实例
file_storage = FileStorageService() 