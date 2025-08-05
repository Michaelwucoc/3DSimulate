from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.models.database import (
    get_db, 
    ReconstructionTask as DBReconstructionTask,
    ReconstructionResult as DBReconstructionResult,
    TaskFile as DBTaskFile,
    UploadedFile as DBUploadedFile
)
from app.schemas.base import (
    ReconstructionTaskCreate,
    ReconstructionTaskResponse,
    TaskStatusResponse,
    ApiResponse
)
from app.services.reconstruction import reconstruction_service
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/reconstruction/create", response_model=ApiResponse)
async def create_reconstruction_task(
    task_data: ReconstructionTaskCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """创建3D重建任务"""
    
    # 临时用户ID
    user_id = "default_user"
    
    try:
        # 验证文件是否存在
        files = db.query(DBUploadedFile).filter(
            DBUploadedFile.id.in_(task_data.file_ids),
            DBUploadedFile.user_id == user_id
        ).all()
        
        if len(files) != len(task_data.file_ids):
            raise HTTPException(status_code=400, detail="部分文件不存在")
        
        # 创建重建任务
        db_task = DBReconstructionTask(
            user_id=user_id,
            method=task_data.method.value,
            quality=task_data.quality.value,
            resolution=task_data.resolution.value,
            status="pending",
            progress=0.0,
            message="任务已创建，等待处理..."
        )
        
        db.add(db_task)
        db.flush()  # 获取任务ID
        
        # 创建任务文件关联
        for file in files:
            task_file = DBTaskFile(
                task_id=db_task.id,
                file_id=file.id
            )
            db.add(task_file)
        
        db.commit()
        
        # 在后台启动重建任务
        background_tasks.add_task(
            process_reconstruction_background,
            db_task.id,
            [file.file_path for file in files],
            task_data.method.value,
            task_data.quality.value,
            task_data.resolution.value
        )
        
        return ApiResponse(
            success=True,
            message="重建任务创建成功",
            data={"task_id": db_task.id}
        )
        
    except Exception as e:
        logger.error(f"创建重建任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建重建任务失败: {str(e)}")

@router.get("/reconstruction/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    db: Session = Depends(get_db)
):
    """获取重建任务状态"""
    
    # 临时用户ID
    user_id = "default_user"
    
    db_task = db.query(DBReconstructionTask).filter(
        DBReconstructionTask.id == task_id,
        DBReconstructionTask.user_id == user_id
    ).first()
    
    if not db_task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 获取任务结果
    result = None
    if db_task.status == "completed":
        db_result = db.query(DBReconstructionResult).filter(
            DBReconstructionResult.task_id == task_id
        ).first()
        
        if db_result:
            result = {
                "id": db_result.id,
                "model_path": db_result.model_path,
                "thumbnail_path": db_result.thumbnail_path,
                "metadata": json.loads(db_result.model_metadata) if db_result.model_metadata else {},
                "statistics": json.loads(db_result.statistics) if db_result.statistics else {},
                "created_at": db_result.created_at
            }
    
    return TaskStatusResponse(
        task_id=db_task.id,
        status=db_task.status,
        progress=db_task.progress,
        message=db_task.message,
        result=result
    )

@router.get("/reconstruction/tasks", response_model=List[ReconstructionTaskResponse])
async def get_tasks(
    db: Session = Depends(get_db)
):
    """获取重建任务列表"""
    
    # 临时用户ID
    user_id = "default_user"
    
    db_tasks = db.query(DBReconstructionTask).filter(
        DBReconstructionTask.user_id == user_id
    ).order_by(DBReconstructionTask.created_at.desc()).all()
    
    tasks = []
    for db_task in db_tasks:
        # 获取任务关联的文件ID
        task_files = db.query(DBTaskFile).filter(
            DBTaskFile.task_id == db_task.id
        ).all()
        file_ids = [tf.file_id for tf in task_files]
        
        task = ReconstructionTaskResponse(
            id=db_task.id,
            method=db_task.method,
            quality=db_task.quality,
            resolution=db_task.resolution,
            status=db_task.status,
            progress=db_task.progress,
            message=db_task.message,
            created_at=db_task.created_at,
            started_at=db_task.started_at,
            completed_at=db_task.completed_at,
            error_message=db_task.error_message,
            file_ids=file_ids
        )
        tasks.append(task)
    
    return tasks

@router.delete("/reconstruction/tasks/{task_id}")
async def delete_task(
    task_id: str,
    db: Session = Depends(get_db)
):
    """删除重建任务"""
    
    # 临时用户ID
    user_id = "default_user"
    
    db_task = db.query(DBReconstructionTask).filter(
        DBReconstructionTask.id == task_id,
        DBReconstructionTask.user_id == user_id
    ).first()
    
    if not db_task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    try:
        # 删除任务文件关联
        db.query(DBTaskFile).filter(
            DBTaskFile.task_id == task_id
        ).delete()
        
        # 删除任务结果
        db.query(DBReconstructionResult).filter(
            DBReconstructionResult.task_id == task_id
        ).delete()
        
        # 删除任务
        db.delete(db_task)
        db.commit()
        
        return ApiResponse(
            success=True,
            message="任务删除成功"
        )
        
    except Exception as e:
        logger.error(f"删除任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除任务失败: {str(e)}")

@router.post("/reconstruction/tasks/{task_id}/restart")
async def restart_task(
    task_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """重新开始重建任务"""
    
    # 临时用户ID
    user_id = "default_user"
    
    db_task = db.query(DBReconstructionTask).filter(
        DBReconstructionTask.id == task_id,
        DBReconstructionTask.user_id == user_id
    ).first()
    
    if not db_task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    try:
        # 重置任务状态
        db_task.status = "pending"
        db_task.progress = 0.0
        db_task.message = "任务重新开始..."
        db_task.started_at = None
        db_task.completed_at = None
        db_task.error_message = None
        
        # 删除之前的结果
        db.query(DBReconstructionResult).filter(
            DBReconstructionResult.task_id == task_id
        ).delete()
        
        db.commit()
        
        # 获取任务文件
        task_files = db.query(DBTaskFile).filter(
            DBTaskFile.task_id == task_id
        ).all()
        
        file_paths = []
        for tf in task_files:
            file = db.query(DBUploadedFile).filter(
                DBUploadedFile.id == tf.file_id
            ).first()
            if file:
                file_paths.append(file.file_path)
        
        # 在后台重新启动任务
        background_tasks.add_task(
            process_reconstruction_background,
            db_task.id,
            file_paths,
            db_task.method,
            db_task.quality,
            db_task.resolution
        )
        
        return ApiResponse(
            success=True,
            message="任务重新开始成功"
        )
        
    except Exception as e:
        logger.error(f"重新开始任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"重新开始任务失败: {str(e)}")

async def process_reconstruction_background(
    task_id: str,
    file_paths: List[str],
    method: str,
    quality: str,
    resolution: str
):
    """后台处理重建任务"""
    
    db = next(get_db())
    
    try:
        # 更新任务状态为处理中
        db_task = db.query(DBReconstructionTask).filter(
            DBReconstructionTask.id == task_id
        ).first()
        
        if db_task:
            db_task.status = "processing"
            db_task.started_at = datetime.now()
            db_task.message = "正在处理中..."
            db.commit()
        
        # 执行重建
        result = await reconstruction_service.process_reconstruction_task(
            task_id, file_paths, method, quality, resolution
        )
        
        # 保存结果
        db_result = DBReconstructionResult(
            task_id=task_id,
            model_path=result["model_path"],
            thumbnail_path=result.get("thumbnail_path"),
            model_metadata=json.dumps(result["metadata"]),
            statistics=json.dumps(result["statistics"])
        )
        
        db.add(db_result)
        
        # 更新任务状态为完成
        if db_task:
            db_task.status = "completed"
            db_task.progress = 100.0
            db_task.completed_at = datetime.now()
            db_task.message = "重建完成"
        
        db.commit()
        
        logger.info(f"重建任务 {task_id} 完成")
        
    except Exception as e:
        logger.error(f"重建任务 {task_id} 失败: {str(e)}")
        
        # 更新任务状态为失败
        db_task = db.query(DBReconstructionTask).filter(
            DBReconstructionTask.id == task_id
        ).first()
        
        if db_task:
            db_task.status = "failed"
            db_task.error_message = str(e)
            db_task.message = "重建失败"
            db.commit()
    
    finally:
        db.close() 