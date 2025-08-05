from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from app.core.config import settings
import uuid

# 创建数据库引擎
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    files = relationship("UploadedFile", back_populates="user")
    tasks = relationship("ReconstructionTask", back_populates="user")

class UploadedFile(Base):
    __tablename__ = "uploaded_files"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String, nullable=False)  # video/image
    mime_type = Column(String, nullable=False)
    user_id = Column(String, ForeignKey("users.id"))
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    is_processed = Column(Boolean, default=False)
    
    # 关系
    user = relationship("User", back_populates="files")
    task_files = relationship("TaskFile", back_populates="file")

class ReconstructionTask(Base):
    __tablename__ = "reconstruction_tasks"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    status = Column(String, nullable=False, default="pending")  # pending, processing, completed, failed
    progress = Column(Float, default=0.0)
    message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    
    # 重建参数
    method = Column(String, default="nerf")  # nerf, gaussian_splatting
    quality = Column(String, default="medium")  # low, medium, high
    resolution = Column(String, default="standard")
    
    # 关系
    user = relationship("User", back_populates="tasks")
    task_files = relationship("TaskFile", back_populates="task")
    result = relationship("ReconstructionResult", back_populates="task", uselist=False)

class TaskFile(Base):
    __tablename__ = "task_files"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    task_id = Column(String, ForeignKey("reconstruction_tasks.id"))
    file_id = Column(String, ForeignKey("uploaded_files.id"))
    
    # 关系
    task = relationship("ReconstructionTask", back_populates="task_files")
    file = relationship("UploadedFile", back_populates="task_files")

class ReconstructionResult(Base):
    __tablename__ = "reconstruction_results"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    task_id = Column(String, ForeignKey("reconstruction_tasks.id"))
    model_path = Column(String, nullable=False)
    thumbnail_path = Column(String)
    model_metadata = Column(Text)  # JSON格式的元数据，重命名避免冲突
    statistics = Column(Text)  # JSON格式的统计信息
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    task = relationship("ReconstructionTask", back_populates="result")

# 数据库依赖
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 创建所有表
def create_tables():
    Base.metadata.create_all(bind=engine) 