from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import uuid
import json
from datetime import datetime
from werkzeug.utils import secure_filename
import subprocess
import threading
import time
from pathlib import Path
import shutil
from typing import Dict, List, Optional

# 导入自定义模块
from services.reconstruction_service import ReconstructionService
from services.file_service import FileService
from services.model_converter import ModelConverter
from utils.config import Config
from utils.logger import setup_logger
from models.task import Task, TaskStatus

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 配置
config = Config()
logger = setup_logger()

# 服务实例
file_service = FileService(config)
reconstruction_service = ReconstructionService(config)
model_converter = ModelConverter(config)

# 全局任务存储（生产环境应使用数据库）
tasks: Dict[str, Task] = {}

# 配置上传文件夹
UPLOAD_FOLDER = config.UPLOAD_FOLDER
OUTPUT_FOLDER = config.OUTPUT_FOLDER
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm', 'jpg', 'jpeg', 'png', 'webp', 'bmp'}

# 确保文件夹存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/upload', methods=['POST'])
def upload_files():
    """文件上传接口"""
    try:
        if 'files' not in request.files:
            return jsonify({'error': '没有文件被上传'}), 400
        
        files = request.files.getlist('files')
        method = request.form.get('method', '3dgs')  # 默认使用3DGS
        
        if not files or all(file.filename == '' for file in files):
            return jsonify({'error': '没有选择文件'}), 400
        
        # 创建任务
        task_id = str(uuid.uuid4())
        task_folder = os.path.join(UPLOAD_FOLDER, task_id)
        os.makedirs(task_folder, exist_ok=True)
        
        uploaded_files = []
        
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # 添加时间戳避免文件名冲突
                name, ext = os.path.splitext(filename)
                filename = f"{name}_{int(time.time())}{ext}"
                
                file_path = os.path.join(task_folder, filename)
                file.save(file_path)
                
                uploaded_files.append({
                    'id': str(uuid.uuid4()),
                    'name': filename,
                    'path': file_path,
                    'size': os.path.getsize(file_path),
                    'type': 'video' if filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')) else 'image'
                })
        
        if not uploaded_files:
            return jsonify({'error': '没有有效的文件被上传'}), 400
        
        # 创建重建任务
        task = Task(
            id=task_id,
            status=TaskStatus.PENDING,
            method=method,
            files=uploaded_files,
            created_at=datetime.now(),
            input_folder=task_folder,
            output_folder=os.path.join(OUTPUT_FOLDER, task_id)
        )
        
        tasks[task_id] = task
        
        logger.info(f"任务 {task_id} 创建成功，上传了 {len(uploaded_files)} 个文件")
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'files': uploaded_files,
            'message': f'成功上传 {len(uploaded_files)} 个文件'
        })
        
    except Exception as e:
        logger.error(f"文件上传失败: {str(e)}")
        return jsonify({'error': f'上传失败: {str(e)}'}), 500

@app.route('/api/tasks/<task_id>/start', methods=['POST'])
def start_reconstruction(task_id):
    """开始3D重建任务"""
    try:
        if task_id not in tasks:
            return jsonify({'error': '任务不存在'}), 404
        
        task = tasks[task_id]
        
        if task.status != TaskStatus.PENDING:
            return jsonify({'error': '任务已经开始或已完成'}), 400
        
        # 更新任务状态
        task.status = TaskStatus.PROCESSING
        task.progress = 0
        task.message = '正在初始化重建任务...'
        task.started_at = datetime.now()
        
        # 在后台线程中执行重建
        thread = threading.Thread(
            target=process_reconstruction_task,
            args=(task_id,)
        )
        thread.daemon = True
        thread.start()
        
        logger.info(f"任务 {task_id} 开始处理")
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'status': task.status.value,
            'message': '重建任务已开始'
        })
        
    except Exception as e:
        logger.error(f"启动重建任务失败: {str(e)}")
        return jsonify({'error': f'启动失败: {str(e)}'}), 500

@app.route('/api/tasks/<task_id>/status', methods=['GET'])
def get_task_status(task_id):
    """获取任务状态"""
    try:
        if task_id not in tasks:
            return jsonify({'error': '任务不存在'}), 404
        
        task = tasks[task_id]
        
        response_data = {
            'task_id': task_id,
            'status': task.status.value,
            'progress': task.progress,
            'message': task.message,
            'method': task.method,
            'created_at': task.created_at.isoformat(),
            'files_count': len(task.files)
        }
        
        if task.started_at:
            response_data['started_at'] = task.started_at.isoformat()
        
        if task.completed_at:
            response_data['completed_at'] = task.completed_at.isoformat()
            response_data['processing_time'] = (task.completed_at - task.started_at).total_seconds()
        
        if task.result:
            response_data['result'] = task.result
        
        if task.error:
            response_data['error'] = task.error
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"获取任务状态失败: {str(e)}")
        return jsonify({'error': f'获取状态失败: {str(e)}'}), 500

@app.route('/api/tasks', methods=['GET'])
def get_all_tasks():
    """获取所有任务列表"""
    try:
        task_list = []
        for task_id, task in tasks.items():
            task_info = {
                'id': task_id,
                'status': task.status.value,
                'progress': task.progress,
                'method': task.method,
                'created_at': task.created_at.isoformat(),
                'files_count': len(task.files)
            }
            
            if task.completed_at:
                task_info['completed_at'] = task.completed_at.isoformat()
            
            task_list.append(task_info)
        
        # 按创建时间倒序排列
        task_list.sort(key=lambda x: x['created_at'], reverse=True)
        
        return jsonify({
            'tasks': task_list,
            'total': len(task_list)
        })
        
    except Exception as e:
        logger.error(f"获取任务列表失败: {str(e)}")
        return jsonify({'error': f'获取任务列表失败: {str(e)}'}), 500

@app.route('/api/tasks/<task_id>/result', methods=['GET'])
def get_task_result(task_id):
    """获取任务结果"""
    try:
        if task_id not in tasks:
            return jsonify({'error': '任务不存在'}), 404
        
        task = tasks[task_id]
        
        if task.status != TaskStatus.COMPLETED:
            return jsonify({'error': '任务尚未完成'}), 400
        
        if not task.result:
            return jsonify({'error': '任务结果不存在'}), 404
        
        return jsonify({
            'success': True,
            'result': task.result
        })
        
    except Exception as e:
        logger.error(f"获取任务结果失败: {str(e)}")
        return jsonify({'error': f'获取结果失败: {str(e)}'}), 500

@app.route('/api/tasks/<task_id>/download/<file_type>', methods=['GET'])
def download_result_file(task_id, file_type):
    """下载结果文件"""
    try:
        if task_id not in tasks:
            return jsonify({'error': '任务不存在'}), 404
        
        task = tasks[task_id]
        
        if task.status != TaskStatus.COMPLETED or not task.result:
            return jsonify({'error': '任务尚未完成或结果不存在'}), 400
        
        # 根据文件类型返回相应文件
        file_path = None
        if file_type == 'model':
            file_path = task.result.get('model_path')
        elif file_type == 'thumbnail':
            file_path = task.result.get('thumbnail_path')
        elif file_type == 'metadata':
            file_path = task.result.get('metadata_path')
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({'error': '文件不存在'}), 404
        
        return send_file(file_path, as_attachment=True)
        
    except Exception as e:
        logger.error(f"下载文件失败: {str(e)}")
        return jsonify({'error': f'下载失败: {str(e)}'}), 500

@app.route('/api/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    """删除任务"""
    try:
        if task_id not in tasks:
            return jsonify({'error': '任务不存在'}), 404
        
        task = tasks[task_id]
        
        # 删除文件夹
        if os.path.exists(task.input_folder):
            shutil.rmtree(task.input_folder)
        
        if os.path.exists(task.output_folder):
            shutil.rmtree(task.output_folder)
        
        # 从内存中删除任务
        del tasks[task_id]
        
        logger.info(f"任务 {task_id} 已删除")
        
        return jsonify({
            'success': True,
            'message': '任务已删除'
        })
        
    except Exception as e:
        logger.error(f"删除任务失败: {str(e)}")
        return jsonify({'error': f'删除失败: {str(e)}'}), 500

def process_reconstruction_task(task_id: str):
    """处理3D重建任务的后台函数"""
    try:
        task = tasks[task_id]
        logger.info(f"开始处理任务 {task_id}")
        
        # 创建输出文件夹
        os.makedirs(task.output_folder, exist_ok=True)
        
        # 根据方法选择不同的重建服务
        if task.method == 'nerf':
            result = reconstruction_service.process_nerf(task)
        elif task.method == '3dgs':
            result = reconstruction_service.process_3dgs(task)
        else:
            raise ValueError(f"不支持的重建方法: {task.method}")
        
        # 更新任务状态
        task.status = TaskStatus.COMPLETED
        task.progress = 100
        task.message = '重建完成！'
        task.completed_at = datetime.now()
        task.result = result
        
        logger.info(f"任务 {task_id} 处理完成")
        
    except Exception as e:
        logger.error(f"任务 {task_id} 处理失败: {str(e)}")
        
        task = tasks[task_id]
        task.status = TaskStatus.FAILED
        task.message = f'处理失败: {str(e)}'
        task.error = str(e)
        task.completed_at = datetime.now()

if __name__ == '__main__':
    logger.info("启动3D重建后端服务...")
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )