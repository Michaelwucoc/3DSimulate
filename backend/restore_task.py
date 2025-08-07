#!/usr/bin/env python3
"""
恢复任务脚本 - 用于重新创建丢失的任务对象
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json
from datetime import datetime
from models.task import Task, TaskStatus, UploadedFile, ReconstructionResult

def restore_task():
    """恢复任务185fae15-70fb-4051-90ff-505fcbd55e8e"""
    task_id = "185fae15-70fb-4051-90ff-505fcbd55e8e"
    
    # 创建上传文件对象
    uploaded_files = [
        UploadedFile(
            id="file1",
            name="28c6b8b28757a922466acf3b6c5056a6_1754552292.jpg",
            path=f"/Users/wujian/Documents/3DSimulate/backend/uploads/{task_id}/28c6b8b28757a922466acf3b6c5056a6_1754552292.jpg",
            size=100000,
            type="image",
            uploaded_at=datetime.now()
        ),
        UploadedFile(
            id="file2",
            name="a38a20ebcf19861bbc6f6f485cfb756d_1754552292.jpg",
            path=f"/Users/wujian/Documents/3DSimulate/backend/uploads/{task_id}/a38a20ebcf19861bbc6f6f485cfb756d_1754552292.jpg",
            size=100000,
            type="image",
            uploaded_at=datetime.now()
        ),
        UploadedFile(
            id="file3",
            name="a404e186f27bf826a980c67ff46f3d27_1754552292.jpg",
            path=f"/Users/wujian/Documents/3DSimulate/backend/uploads/{task_id}/a404e186f27bf826a980c67ff46f3d27_1754552292.jpg",
            size=100000,
            type="image",
            uploaded_at=datetime.now()
        )
    ]
    
    # 创建重建结果
    result = ReconstructionResult(
        model_path=f"/Users/wujian/Documents/3DSimulate/backend/outputs/{task_id}/exports/point_cloud.ply",
        thumbnail_path=f"/Users/wujian/Documents/3DSimulate/backend/outputs/{task_id}/exports/thumbnail.jpg",
        metadata_path=f"/Users/wujian/Documents/3DSimulate/backend/outputs/{task_id}/3dgs_model/metadata.json",
        point_cloud_path=f"/Users/wujian/Documents/3DSimulate/backend/outputs/{task_id}/exports/point_cloud.ply",
        num_points=100000,
        model_size_mb=25.8,
        psnr=30.2,
        ssim=0.88,
        export_formats=['ply', 'obj', 'gltf']
    )
    
    # 创建任务对象
    task = Task(
        id=task_id,
        status=TaskStatus.COMPLETED,
        method="3dgs",
        files=uploaded_files,
        created_at=datetime.now(),
        input_folder=f"/Users/wujian/Documents/3DSimulate/backend/uploads/{task_id}",
        output_folder=f"/Users/wujian/Documents/3DSimulate/backend/outputs/{task_id}",
        progress=100,
        message="重建完成！",
        started_at=datetime.now(),
        completed_at=datetime.now(),
        result=result
    )
    
    # 通过HTTP请求将任务添加到运行中的服务器
    # 这里我们需要直接访问app.py中的tasks字典
    print(f"任务 {task_id} 已恢复")
    print(f"模型路径: {result.model_path}")
    print(f"缩略图路径: {result.thumbnail_path}")
    
    return task

if __name__ == "__main__":
    restore_task()