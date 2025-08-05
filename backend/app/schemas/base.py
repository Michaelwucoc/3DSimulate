from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class FileType(str, Enum):
    VIDEO = "video"
    IMAGE = "image"

class ReconstructionMethod(str, Enum):
    NERF = "nerf"
    GAUSSIAN_SPLATTING = "gaussian_splatting"

class QualityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class ResolutionLevel(str, Enum):
    LOW = "low"
    STANDARD = "standard"
    HIGH = "high"

class BaseSchema(BaseModel):
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class UploadedFileBase(BaseSchema):
    filename: str
    original_filename: str
    file_size: int
    file_type: FileType
    mime_type: str

class UploadedFileCreate(UploadedFileBase):
    pass

class UploadedFileResponse(UploadedFileBase):
    id: str
    uploaded_at: datetime
    is_processed: bool

class ReconstructionTaskBase(BaseSchema):
    method: ReconstructionMethod = ReconstructionMethod.NERF
    quality: QualityLevel = QualityLevel.MEDIUM
    resolution: ResolutionLevel = ResolutionLevel.STANDARD

class ReconstructionTaskCreate(ReconstructionTaskBase):
    file_ids: List[str]

class ReconstructionTaskUpdate(BaseSchema):
    status: Optional[TaskStatus] = None
    progress: Optional[float] = None
    message: Optional[str] = None
    error_message: Optional[str] = None

class ReconstructionTaskResponse(ReconstructionTaskBase):
    id: str
    status: TaskStatus
    progress: float
    message: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    file_ids: List[str]

class ReconstructionResultBase(BaseSchema):
    model_path: str
    thumbnail_path: Optional[str]
    metadata: Dict[str, Any]
    statistics: Dict[str, Any]

class ReconstructionResultCreate(ReconstructionResultBase):
    task_id: str

class ReconstructionResultResponse(ReconstructionResultBase):
    id: str
    created_at: datetime

class TaskStatusResponse(BaseSchema):
    task_id: str
    status: TaskStatus
    progress: float
    message: Optional[str]
    result: Optional[ReconstructionResultResponse]

class ApiResponse(BaseSchema):
    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None
    error: Optional[str] = None

class UploadResponse(BaseSchema):
    task_id: str
    files: List[UploadedFileResponse]

class ErrorResponse(BaseSchema):
    detail: str
    error_code: Optional[str] = None 