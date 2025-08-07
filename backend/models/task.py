from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
import json

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = 'pending'          # 等待开始
    PROCESSING = 'processing'    # 处理中
    COMPLETED = 'completed'      # 已完成
    FAILED = 'failed'           # 失败
    CANCELLED = 'cancelled'      # 已取消

class ReconstructionMethod(Enum):
    """重建方法枚举"""
    NERF = 'nerf'               # Neural Radiance Fields
    GAUSSIAN_SPLATTING = '3dgs'  # 3D Gaussian Splatting
    INSTANT_NGP = 'instant-ngp'  # Instant Neural Graphics Primitives
    MIPNERF = 'mipnerf'         # Mip-NeRF

@dataclass
class UploadedFile:
    """上传文件信息"""
    id: str
    name: str
    path: str
    size: int
    type: str  # 'video' or 'image'
    mime_type: Optional[str] = None
    uploaded_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'path': self.path,
            'size': self.size,
            'type': self.type,
            'mime_type': self.mime_type,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None
        }

@dataclass
class ProcessingStep:
    """处理步骤信息"""
    name: str
    status: str  # 'pending', 'running', 'completed', 'failed'
    progress: int = 0
    message: str = ''
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'status': self.status,
            'progress': self.progress,
            'message': self.message,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error': self.error
        }

@dataclass
class ReconstructionResult:
    """重建结果信息"""
    model_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    metadata_path: Optional[str] = None
    point_cloud_path: Optional[str] = None
    mesh_path: Optional[str] = None
    texture_path: Optional[str] = None
    
    # 模型统计信息
    num_points: Optional[int] = None
    num_faces: Optional[int] = None
    model_size_mb: Optional[float] = None
    
    # 质量指标
    psnr: Optional[float] = None
    ssim: Optional[float] = None
    lpips: Optional[float] = None
    
    # 渲染配置
    render_config: Optional[Dict[str, Any]] = None
    
    # 导出格式
    export_formats: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'model_path': self.model_path,
            'thumbnail_path': self.thumbnail_path,
            'metadata_path': self.metadata_path,
            'point_cloud_path': self.point_cloud_path,
            'mesh_path': self.mesh_path,
            'texture_path': self.texture_path,
            'num_points': self.num_points,
            'num_faces': self.num_faces,
            'model_size_mb': self.model_size_mb,
            'psnr': self.psnr,
            'ssim': self.ssim,
            'lpips': self.lpips,
            'render_config': self.render_config,
            'export_formats': self.export_formats
        }

@dataclass
class Task:
    """3D重建任务"""
    id: str
    status: TaskStatus
    method: str  # 重建方法
    files: List[UploadedFile]
    created_at: datetime
    input_folder: str
    output_folder: str
    
    # 可选字段
    name: Optional[str] = None
    description: Optional[str] = None
    progress: int = 0
    message: str = ''
    
    # 时间戳
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # 处理步骤
    steps: List[ProcessingStep] = field(default_factory=list)
    
    # 结果和错误
    result: Optional[ReconstructionResult] = None
    error: Optional[str] = None
    
    # 配置参数
    config: Dict[str, Any] = field(default_factory=dict)
    
    # 性能指标
    processing_time: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    gpu_usage_percent: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'status': self.status.value,
            'method': self.method,
            'name': self.name,
            'description': self.description,
            'progress': self.progress,
            'message': self.message,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'files': [f.to_dict() for f in self.files],
            'steps': [s.to_dict() for s in self.steps],
            'result': self.result.to_dict() if self.result else None,
            'error': self.error,
            'config': self.config,
            'processing_time': self.processing_time,
            'memory_usage_mb': self.memory_usage_mb,
            'gpu_usage_percent': self.gpu_usage_percent,
            'input_folder': self.input_folder,
            'output_folder': self.output_folder
        }
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
    
    def add_step(self, name: str, message: str = '') -> ProcessingStep:
        """添加处理步骤"""
        step = ProcessingStep(
            name=name,
            status='pending',
            message=message
        )
        self.steps.append(step)
        return step
    
    def start_step(self, step_name: str) -> Optional[ProcessingStep]:
        """开始执行步骤"""
        for step in self.steps:
            if step.name == step_name:
                step.status = 'running'
                step.started_at = datetime.now()
                return step
        return None
    
    def complete_step(self, step_name: str, message: str = '') -> Optional[ProcessingStep]:
        """完成步骤"""
        for step in self.steps:
            if step.name == step_name:
                step.status = 'completed'
                step.progress = 100
                step.completed_at = datetime.now()
                if message:
                    step.message = message
                return step
        return None
    
    def fail_step(self, step_name: str, error: str) -> Optional[ProcessingStep]:
        """步骤失败"""
        for step in self.steps:
            if step.name == step_name:
                step.status = 'failed'
                step.completed_at = datetime.now()
                step.error = error
                return step
        return None
    
    def update_step_progress(self, step_name: str, progress: int, message: str = '') -> Optional[ProcessingStep]:
        """更新步骤进度"""
        for step in self.steps:
            if step.name == step_name:
                step.progress = min(100, max(0, progress))
                if message:
                    step.message = message
                return step
        return None
    
    def get_current_step(self) -> Optional[ProcessingStep]:
        """获取当前正在执行的步骤"""
        for step in self.steps:
            if step.status == 'running':
                return step
        return None
    
    def calculate_overall_progress(self) -> int:
        """计算总体进度"""
        if not self.steps:
            return self.progress
        
        total_progress = sum(step.progress for step in self.steps)
        return min(100, total_progress // len(self.steps))
    
    def is_processing(self) -> bool:
        """检查是否正在处理"""
        return self.status == TaskStatus.PROCESSING
    
    def is_completed(self) -> bool:
        """检查是否已完成"""
        return self.status == TaskStatus.COMPLETED
    
    def is_failed(self) -> bool:
        """检查是否失败"""
        return self.status == TaskStatus.FAILED
    
    def can_start(self) -> bool:
        """检查是否可以开始"""
        return self.status == TaskStatus.PENDING
    
    def can_cancel(self) -> bool:
        """检查是否可以取消"""
        return self.status in [TaskStatus.PENDING, TaskStatus.PROCESSING]
    
    def start(self):
        """开始任务"""
        if self.can_start():
            self.status = TaskStatus.PROCESSING
            self.started_at = datetime.now()
            self.progress = 0
            self.message = '任务开始处理...'
    
    def complete(self, result: ReconstructionResult = None):
        """完成任务"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        self.progress = 100
        self.message = '任务处理完成'
        
        if result:
            self.result = result
        
        if self.started_at:
            self.processing_time = (self.completed_at - self.started_at).total_seconds()
    
    def fail(self, error: str):
        """任务失败"""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now()
        self.error = error
        self.message = f'任务处理失败: {error}'
        
        if self.started_at:
            self.processing_time = (self.completed_at - self.started_at).total_seconds()
    
    def cancel(self):
        """取消任务"""
        if self.can_cancel():
            self.status = TaskStatus.CANCELLED
            self.completed_at = datetime.now()
            self.message = '任务已取消'
            
            if self.started_at:
                self.processing_time = (self.completed_at - self.started_at).total_seconds()

@dataclass
class TaskSummary:
    """任务摘要信息（用于列表显示）"""
    id: str
    status: str
    method: str
    progress: int
    created_at: str
    files_count: int
    name: Optional[str] = None
    completed_at: Optional[str] = None
    processing_time: Optional[float] = None
    
    @classmethod
    def from_task(cls, task: Task) -> 'TaskSummary':
        """从Task对象创建摘要"""
        return cls(
            id=task.id,
            status=task.status.value,
            method=task.method,
            progress=task.progress,
            created_at=task.created_at.isoformat(),
            files_count=len(task.files),
            name=task.name,
            completed_at=task.completed_at.isoformat() if task.completed_at else None,
            processing_time=task.processing_time
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'status': self.status,
            'method': self.method,
            'progress': self.progress,
            'created_at': self.created_at,
            'files_count': self.files_count,
            'name': self.name,
            'completed_at': self.completed_at,
            'processing_time': self.processing_time
        }