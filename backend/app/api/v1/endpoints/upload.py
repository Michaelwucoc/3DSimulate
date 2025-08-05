from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List
from sqlalchemy.orm import Session
from app.models.database import get_db, UploadedFile as DBUploadedFile
from app.services.storage import file_storage
from app.schemas.base import UploadResponse, UploadedFileResponse, ApiResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/upload", response_model=UploadResponse)
async def upload_files(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """上传文件"""
    
    if not files:
        raise HTTPException(status_code=400, detail="没有选择文件")
    
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="最多只能上传10个文件")
    
    try:
        # 临时用户ID（实际应用中应该从认证中获取）
        user_id = "default_user"
        
        # 保存文件
        saved_files = await file_storage.save_multiple_files(files, user_id)
        
        # 保存到数据库
        db_files = []
        for file_info in saved_files:
            db_file = DBUploadedFile(
                id=file_info["id"],
                filename=file_info["filename"],
                original_filename=file_info["original_filename"],
                file_path=file_info["file_path"],
                file_size=file_info["file_size"],
                file_type=file_info["file_type"],
                mime_type=file_info["mime_type"],
                user_id=user_id
            )
            db.add(db_file)
            db_files.append(db_file)
        
        db.commit()
        
        # 返回响应
        uploaded_files = [
            UploadedFileResponse(
                id=file.id,
                filename=file.filename,
                original_filename=file.original_filename,
                file_size=file.file_size,
                file_type=file.file_type,
                mime_type=file.mime_type,
                uploaded_at=file.uploaded_at,
                is_processed=file.is_processed
            )
            for file in db_files
        ]
        
        return UploadResponse(
            task_id="",  # 这里应该创建重建任务
            files=uploaded_files
        )
        
    except Exception as e:
        logger.error(f"文件上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

@router.get("/files", response_model=List[UploadedFileResponse])
async def get_uploaded_files(
    db: Session = Depends(get_db)
):
    """获取已上传的文件列表"""
    
    # 临时用户ID
    user_id = "default_user"
    
    db_files = db.query(DBUploadedFile).filter(
        DBUploadedFile.user_id == user_id
    ).all()
    
    return [
        UploadedFileResponse(
            id=file.id,
            filename=file.filename,
            original_filename=file.original_filename,
            file_size=file.file_size,
            file_type=file.file_type,
            mime_type=file.mime_type,
            uploaded_at=file.uploaded_at,
            is_processed=file.is_processed
        )
        for file in db_files
    ]

@router.delete("/files/{file_id}")
async def delete_file(
    file_id: str,
    db: Session = Depends(get_db)
):
    """删除上传的文件"""
    
    # 临时用户ID
    user_id = "default_user"
    
    # 查找文件
    db_file = db.query(DBUploadedFile).filter(
        DBUploadedFile.id == file_id,
        DBUploadedFile.user_id == user_id
    ).first()
    
    if not db_file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    try:
        # 删除物理文件
        if file_storage.delete_file(file_id, user_id):
            # 删除数据库记录
            db.delete(db_file)
            db.commit()
            
            return ApiResponse(
                success=True,
                message="文件删除成功"
            )
        else:
            raise HTTPException(status_code=500, detail="文件删除失败")
            
    except Exception as e:
        logger.error(f"删除文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除文件失败: {str(e)}")

@router.get("/storage/info")
async def get_storage_info():
    """获取存储信息"""
    
    try:
        info = file_storage.get_storage_info()
        return ApiResponse(
            success=True,
            data=info
        )
    except Exception as e:
        logger.error(f"获取存储信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取存储信息失败: {str(e)}") 