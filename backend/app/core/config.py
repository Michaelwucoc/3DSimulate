from pydantic_settings import BaseSettings
from typing import Optional, List
import os

class Settings(BaseSettings):
    # 应用基本配置
    app_name: str = "3D场景重建平台"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000
    
    # 数据库配置
    database_url: str = "sqlite:///./3d_reconstruction.db"
    
    # Redis配置
    redis_url: str = "redis://localhost:6379/0"
    
    
    # 文件存储配置
    upload_dir: str = "./uploads"
    models_dir: str = "./models"
    max_file_size: int = 500 * 1024 * 1024  # 500MB
    allowed_file_types: List[str] = [
        "video/mp4", "video/avi", "video/mov", "video/wmv", "video/flv", "video/webm",
        "image/jpeg", "image/jpg", "image/png", "image/webp"
    ]
    
    # 3D重建配置
    reconstruction_timeout: int = 3600  # 1小时
    max_concurrent_reconstructions: int = 3
    gpu_memory_limit: Optional[int] = None  # GB
    
    # 安全配置
    secret_key: str = "your-secret-key-here"
    access_token_expire_minutes: int = 30
    
    # CORS配置
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ]
    
    # 日志配置
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# 创建全局设置实例
settings = Settings()

# 确保必要的目录存在
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.models_dir, exist_ok=True)
os.makedirs("temp", exist_ok=True) 