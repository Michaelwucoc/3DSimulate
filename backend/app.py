from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import os
import uuid
import json
import sys
from datetime import datetime
from werkzeug.utils import secure_filename
import subprocess
import threading
import time
from pathlib import Path
import shutil
from typing import Dict, List, Optional

# 添加tools目录到Python路径
project_root = Path(__file__).parent.parent
tools_dir = project_root / "tools"
sys.path.insert(0, str(tools_dir))

# 导入自定义模块
from services.reconstruction_service import ReconstructionService
from services.file_service import FileService
from services.model_converter import ModelConverter
from utils.config import Config
from utils.logger import setup_logger
from models.task import Task, TaskStatus, UploadedFile

# 尝试导入深度分析模块
try:
    from depth_analysis import DepthAnalyzer
    depth_analyzer_available = True
except ImportError:
    depth_analyzer_available = False

# 全局变量
tasks: Dict[str, Task] = {}

def generate_task_id():
    """生成唯一的任务ID"""
    return str(uuid.uuid4())

def create_app():
    """创建Flask应用实例"""
    app = Flask(__name__)
    CORS(app)  # 允许跨域请求
    
    # 配置
    config = Config()
    logger = setup_logger()
    
    # 服务实例
    file_service = FileService(config)
    reconstruction_service = ReconstructionService(config)
    model_converter = ModelConverter(config)
    
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
                    
                    uploaded_file = UploadedFile(
                        id=str(uuid.uuid4()),
                        name=filename,
                        path=file_path,
                        size=os.path.getsize(file_path),
                        type='video' if filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')) else 'image',
                        uploaded_at=datetime.now()
                    )
                    uploaded_files.append(uploaded_file)
            
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
                # 转换文件路径为URL
                result_dict = task.result.to_dict()
                if result_dict.get('model_path'):
                    result_dict['modelUrl'] = f"http://127.0.0.1:8000/api/files/{task_id}/model.ply"
                if result_dict.get('thumbnail_path'):
                    result_dict['thumbnailUrl'] = f"http://127.0.0.1:8000/api/files/{task_id}/thumbnail.jpg"
                response_data['result'] = result_dict
            
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
                model_path = task.result.get('model_path')
                if model_path:
                    # 检查model_path是否为目录（3DGS情况）
                    if os.path.isdir(model_path):
                        # 对于3DGS，在目录中查找point_cloud.ply文件
                        ply_file_path = os.path.join(model_path, 'point_cloud.ply')
                        if os.path.exists(ply_file_path):
                            file_path = ply_file_path
                    else:
                        # 对于其他方法，直接使用model_path
                        file_path = model_path
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

    @app.route('/api/files/<task_id>/<filename>', methods=['GET'])
    def serve_file(task_id, filename):
        """提供文件服务"""
        try:
            if task_id not in tasks:
                return jsonify({'error': '任务不存在'}), 404
            
            task = tasks[task_id]
            
            # 根据文件名确定文件路径
            if filename == 'model.ply':
                if task.result and task.result.model_path:
                    # 检查model_path是否为目录（3DGS情况）
                    if os.path.isdir(task.result.model_path):
                        # 对于3DGS，在目录中查找point_cloud.ply文件
                        ply_file_path = os.path.join(task.result.model_path, 'point_cloud.ply')
                        if os.path.exists(ply_file_path):
                            return send_file(ply_file_path, as_attachment=False)
                        else:
                            return jsonify({'error': 'PLY文件不存在'}), 404
                    else:
                        # 对于其他方法，直接使用model_path
                        return send_file(task.result.model_path, as_attachment=False)
            elif filename == 'thumbnail.jpg':
                if task.result and task.result.thumbnail_path:
                    return send_file(task.result.thumbnail_path, as_attachment=False)
            
            return jsonify({'error': '文件不存在'}), 404
            
        except Exception as e:
            logger.error(f"文件服务失败: {str(e)}")
            return jsonify({'error': f'文件服务失败: {str(e)}'}), 500

    # 深度分析相关的全局状态
    depth_analysis_tasks = {}
    depth_analyzer_instance = None

    @app.route('/api/depth/upload', methods=['POST'])
    def upload_depth_data():
        """上传深度分析数据"""
        if not depth_analyzer_available:
            return jsonify({'error': '深度分析模块未安装'}), 500
            
        try:
            task_id = generate_task_id()
            task_dir = os.path.join(UPLOAD_FOLDER, task_id)
            os.makedirs(task_dir, exist_ok=True)
            
            # 创建子目录
            images_dir = os.path.join(task_dir, 'images')
            depths_dir = os.path.join(task_dir, 'depths')
            os.makedirs(images_dir, exist_ok=True)
            os.makedirs(depths_dir, exist_ok=True)
            
            uploaded_files = {'images': [], 'depths': [], 'intrinsics': None, 'extrinsics': None}
            
            # 处理图像文件
            if 'images' in request.files:
                image_files = request.files.getlist('images')
                for i, file in enumerate(image_files):
                    if file and file.filename:
                        ext = file.filename.rsplit('.', 1)[1].lower()
                        if ext in ['jpg', 'jpeg', 'png']:
                            filename = f"image_{i:04d}.{ext}"
                            filepath = os.path.join(images_dir, filename)
                            file.save(filepath)
                            uploaded_files['images'].append(filepath)
            
            # 处理深度文件
            if 'depths' in request.files:
                depth_files = request.files.getlist('depths')
                for i, file in enumerate(depth_files):
                    if file and file.filename:
                        ext = file.filename.rsplit('.', 1)[1].lower()
                        if ext in ['npy', 'png']:
                            filename = f"depth_{i:04d}.{ext}"
                            filepath = os.path.join(depths_dir, filename)
                            file.save(filepath)
                            uploaded_files['depths'].append(filepath)
            
            # 处理内参文件
            if 'intrinsics' in request.files:
                intrinsics_file = request.files['intrinsics']
                if intrinsics_file and intrinsics_file.filename:
                    ext = intrinsics_file.filename.rsplit('.', 1)[1].lower()
                    if ext in ['npy', 'json']:
                        filename = f"intrinsics.{ext}"
                        filepath = os.path.join(task_dir, filename)
                        intrinsics_file.save(filepath)
                        uploaded_files['intrinsics'] = filepath
            
            # 处理外参文件
            if 'extrinsics' in request.files:
                extrinsics_file = request.files['extrinsics']
                if extrinsics_file and extrinsics_file.filename:
                    ext = extrinsics_file.filename.rsplit('.', 1)[1].lower()
                    if ext in ['npy', 'json']:
                        filename = f"extrinsics.{ext}"
                        filepath = os.path.join(task_dir, filename)
                        extrinsics_file.save(filepath)
                        uploaded_files['extrinsics'] = filepath
            
            # 验证上传文件
            if not uploaded_files['images'] or not uploaded_files['depths']:
                return jsonify({'error': '缺少图像或深度文件'}), 400
            
            if not uploaded_files['intrinsics'] or not uploaded_files['extrinsics']:
                return jsonify({'error': '缺少相机内参或外参文件'}), 400
            
            # 创建深度分析任务
            depth_task = {
                'id': task_id,
                'status': 'uploaded',
                'progress': 0,
                'message': '文件上传完成',
                'files': uploaded_files,
                'created_at': datetime.now().isoformat(),
                'output_dir': os.path.join(OUTPUT_FOLDER, task_id)
            }
            
            depth_analysis_tasks[task_id] = depth_task
            os.makedirs(depth_task['output_dir'], exist_ok=True)
            
            return jsonify({
                'task_id': task_id,
                'message': '深度分析数据上传成功',
                'files_count': {
                    'images': len(uploaded_files['images']),
                    'depths': len(uploaded_files['depths'])
                }
            })
            
        except Exception as e:
            logger.error(f"深度数据上传失败: {str(e)}")
            return jsonify({'error': f'上传失败: {str(e)}'}), 500

    @app.route('/api/depth/tasks/<task_id>/start', methods=['POST'])
    def start_depth_analysis(task_id):
        """启动深度分析任务"""
        if not depth_analyzer_available:
            return jsonify({'error': '深度分析模块未安装'}), 500
            
        if task_id not in depth_analysis_tasks:
            return jsonify({'error': '任务不存在'}), 404
            
        task = depth_analysis_tasks[task_id]
        if task['status'] == 'processing':
            return jsonify({'error': '任务已在处理中'}), 400
            
        try:
            data = request.get_json() or {}
            analysis_options = {
                'visualization': data.get('visualization', ['open3d']),
                'colmap': data.get('colmap', False),
                'monocular_depth': data.get('monocular_depth', None),
                'port': data.get('port', 8081)
            }
            
            # 更新任务状态
            task['status'] = 'processing'
            task['progress'] = 10
            task['message'] = '正在初始化深度分析...'
            task['analysis_options'] = analysis_options
            
            # 异步启动深度分析
            def run_depth_analysis():
                try:
                    # 创建深度分析器
                    analyzer = DepthAnalyzer(
                        data_dir=os.path.join(UPLOAD_FOLDER, task_id),
                        output_dir=task['output_dir']
                    )
                    
                    # 加载相机数据
                    task['progress'] = 20
                    task['message'] = '正在加载相机数据...'
                    
                    analyzer.load_camera_data(
                        image_dir=os.path.join(UPLOAD_FOLDER, task_id, 'images'),
                        depth_dir=os.path.join(UPLOAD_FOLDER, task_id, 'depths'),
                        intrinsics_file=task['files']['intrinsics'],
                        extrinsics_file=task['files']['extrinsics']
                    )
                    
                    # 分析深度特征
                    task['progress'] = 40
                    task['message'] = '正在分析深度特征...'
                    analyzer.analyze_depth_characteristics()
                    
                    # 可视化处理
                    task['progress'] = 60
                    task['message'] = '正在生成可视化...'
                    
                    results = {}
                    
                    # ScenePic可视化（生成HTML）
                    if 'scenepic' in analysis_options['visualization']:
                        try:
                            analyzer.visualize_with_scenepic()
                            scenepic_path = os.path.join(task['output_dir'], 'scenepic_visualization.html')
                            if os.path.exists(scenepic_path):
                                results['scenepic_html'] = f"/api/depth/tasks/{task_id}/files/scenepic_visualization.html"
                        except Exception as e:
                            logger.warning(f"ScenePic visualization failed: {e}")
                    
                    # COLMAP处理
                    if analysis_options['colmap']:
                        task['progress'] = 70
                        task['message'] = '正在运行COLMAP...'
                        try:
                            analyzer.run_colmap()
                            results['colmap_completed'] = True
                        except Exception as e:
                            logger.warning(f"COLMAP processing failed: {e}")
                            results['colmap_error'] = str(e)
                    
                    # 单目深度估计
                    if analysis_options['monocular_depth']:
                        task['progress'] = 80
                        task['message'] = f'正在运行{analysis_options["monocular_depth"]}深度估计...'
                        try:
                            analyzer.estimate_monocular_depth(analysis_options['monocular_depth'])
                            results['monocular_depth_completed'] = True
                        except Exception as e:
                            logger.warning(f"Monocular depth estimation failed: {e}")
                            results['monocular_depth_error'] = str(e)
                    
                    # 完成
                    task['status'] = 'completed'
                    task['progress'] = 100
                    task['message'] = '深度分析完成'
                    task['results'] = results
                    
                    # 检查生成的文件
                    output_files = []
                    for root, dirs, files in os.walk(task['output_dir']):
                        for file in files:
                            if file.endswith(('.png', '.html', '.npy', '.ply')):
                                rel_path = os.path.relpath(os.path.join(root, file), task['output_dir'])
                                output_files.append(rel_path)
                    
                    task['output_files'] = output_files
                    
                except Exception as e:
                    task['status'] = 'failed'
                    task['message'] = f'分析失败: {str(e)}'
                    logger.error(f"Depth analysis failed for task {task_id}: {str(e)}")
            
            # 在新线程中运行分析
            import threading
            analysis_thread = threading.Thread(target=run_depth_analysis)
            analysis_thread.daemon = True
            analysis_thread.start()
            
            return jsonify({'message': '深度分析已启动', 'task_id': task_id})
            
        except Exception as e:
            task['status'] = 'failed'
            task['message'] = f'启动失败: {str(e)}'
            logger.error(f"Failed to start depth analysis: {str(e)}")
            return jsonify({'error': f'启动失败: {str(e)}'}), 500

    @app.route('/api/depth/tasks/<task_id>/status', methods=['GET'])
    def get_depth_analysis_status(task_id):
        """获取深度分析任务状态"""
        if task_id not in depth_analysis_tasks:
            return jsonify({'error': '任务不存在'}), 404
            
        task = depth_analysis_tasks[task_id]
        return jsonify({
            'task_id': task_id,
            'status': task['status'],
            'progress': task['progress'],
            'message': task['message'],
            'results': task.get('results', {}),
            'output_files': task.get('output_files', []),
            'created_at': task['created_at']
        })

    @app.route('/api/depth/tasks', methods=['GET'])
    def get_depth_analysis_tasks():
        """获取所有深度分析任务"""
        tasks_list = []
        for task_id, task in depth_analysis_tasks.items():
            tasks_list.append({
                'task_id': task_id,
                'status': task['status'],
                'progress': task['progress'],
                'message': task['message'],
                'created_at': task['created_at'],
                'files_count': {
                    'images': len(task['files']['images']),
                    'depths': len(task['files']['depths'])
                } if 'files' in task else {}
            })
        
        return jsonify({'tasks': tasks_list})

    @app.route('/api/depth/tasks/<task_id>/files/<path:filename>', methods=['GET'])
    def serve_depth_analysis_file(task_id, filename):
        """提供深度分析结果文件"""
        if task_id not in depth_analysis_tasks:
            return jsonify({'error': '任务不存在'}), 404
            
        task = depth_analysis_tasks[task_id]
        file_path = os.path.join(task['output_dir'], filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': '文件不存在'}), 404
            
        # 安全检查：确保文件在任务输出目录内
        if not os.path.abspath(file_path).startswith(os.path.abspath(task['output_dir'])):
            return jsonify({'error': '无效的文件路径'}), 400
            
        try:
            return send_file(file_path, as_attachment=False)
        except Exception as e:
            logger.error(f"Failed to serve file {file_path}: {str(e)}")
            return jsonify({'error': '文件服务失败'}), 500

    @app.route('/api/depth/tasks/<task_id>/viser', methods=['POST'])
    def start_viser_visualization(task_id):
        """启动Viser可视化服务器"""
        if not depth_analyzer_available:
            return jsonify({'error': '深度分析模块未安装'}), 500
            
        if task_id not in depth_analysis_tasks:
            return jsonify({'error': '任务不存在'}), 404
            
        task = depth_analysis_tasks[task_id]
        if task['status'] != 'completed':
            return jsonify({'error': '任务未完成，无法启动可视化'}), 400
            
        try:
            data = request.get_json() or {}
            port = data.get('port', 8081)
            
            # 检查端口是否已被使用
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            
            if result == 0:
                return jsonify({'error': f'端口 {port} 已被占用'}), 400
            
            def start_viser():
                try:
                    # 重新创建分析器并加载数据
                    analyzer = DepthAnalyzer(
                        data_dir=os.path.join(UPLOAD_FOLDER, task_id),
                        output_dir=task['output_dir']
                    )
                    
                    analyzer.load_camera_data(
                        image_dir=os.path.join(UPLOAD_FOLDER, task_id, 'images'),
                        depth_dir=os.path.join(UPLOAD_FOLDER, task_id, 'depths'),
                        intrinsics_file=task['files']['intrinsics'],
                        extrinsics_file=task['files']['extrinsics']
                    )
                    
                    # 启动Viser服务器（这会阻塞直到服务器停止）
                    analyzer.visualize_with_viser(port)
                    
                except Exception as e:
                    logger.error(f"Viser visualization failed: {str(e)}")
            
            # 在新线程中启动Viser
            import threading
            viser_thread = threading.Thread(target=start_viser)  
            viser_thread.daemon = True
            viser_thread.start()
            
            return jsonify({
                'message': 'Viser可视化服务器已启动',
                'url': f'http://localhost:{port}',
                'port': port
            })
            
        except Exception as e:
            logger.error(f"Failed to start Viser: {str(e)}")
            return jsonify({'error': f'启动Viser失败: {str(e)}'}), 500

    # 返回Flask应用实例
    return app