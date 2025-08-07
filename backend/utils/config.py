import os
from pathlib import Path

class Config:
    """应用配置类"""
    
    def __init__(self):
        # 基础路径
        self.BASE_DIR = Path(__file__).parent.parent
        
        # 服务器配置
        self.HOST = os.getenv('HOST', '0.0.0.0')
        self.PORT = int(os.getenv('PORT', 8000))
        self.DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
        
        # 文件存储配置
        self.UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', str(self.BASE_DIR / 'uploads'))
        self.OUTPUT_FOLDER = os.getenv('OUTPUT_FOLDER', str(self.BASE_DIR / 'outputs'))
        self.TEMP_FOLDER = os.getenv('TEMP_FOLDER', str(self.BASE_DIR / 'temp'))
        
        # 文件大小限制 (字节)
        self.MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 500 * 1024 * 1024))  # 500MB
        self.MAX_FILES_PER_TASK = int(os.getenv('MAX_FILES_PER_TASK', 100))
        
        # NeRF 配置
        self.NERF_CONFIG = {
            'method': 'nerfacto',  # nerfacto, instant-ngp, mipnerf
            'max_num_iterations': int(os.getenv('NERF_MAX_ITERATIONS', 30000)),
            'viewer_port': int(os.getenv('NERF_VIEWER_PORT', 7007)),
            'data_parser': 'colmap',  # colmap, polycam, record3d
            'pipeline': {
                'datamanager': {
                    'camera_optimizer': {
                        'mode': 'SO3xR3'
                    }
                }
            }
        }
        
        # 3D Gaussian Splatting 配置
        self.GAUSSIAN_SPLATTING_CONFIG = {
            'iterations': int(os.getenv('GS_ITERATIONS', 30000)),
            'resolution': int(os.getenv('GS_RESOLUTION', -1)),
            'data_device': 'cuda',
            'white_background': False,
            'sh_degree': 3,
            'convert_SHs_python': False,
            'compute_cov3D_python': False,
            'debug': False
        }
        
        # COLMAP 配置
        self.COLMAP_CONFIG = {
            'feature_type': 'sift',  # sift, superpoint
            'matcher_type': 'exhaustive',  # exhaustive, sequential, vocab_tree
            'num_threads': int(os.getenv('COLMAP_THREADS', -1)),  # -1 表示使用所有可用线程
            'gpu_index': '0',
            'quality': 'high'  # low, medium, high, extreme
        }
        
        # 模型转换配置
        self.CONVERSION_CONFIG = {
            'output_formats': ['ply', 'obj', 'gltf'],  # 支持的输出格式
            'texture_size': int(os.getenv('TEXTURE_SIZE', 1024)),
            'mesh_resolution': float(os.getenv('MESH_RESOLUTION', 512)),
            'point_cloud_size': int(os.getenv('POINT_CLOUD_SIZE', 100000))
        }
        
        # 渲染配置
        self.RENDER_CONFIG = {
            'image_width': int(os.getenv('RENDER_WIDTH', 800)),
            'image_height': int(os.getenv('RENDER_HEIGHT', 600)),
            'fps': int(os.getenv('RENDER_FPS', 24)),
            'num_frames': int(os.getenv('RENDER_FRAMES', 120)),
            'camera_path_type': 'spiral'  # spiral, interpolate, orbit
        }
        
        # 日志配置
        self.LOG_CONFIG = {
            'level': os.getenv('LOG_LEVEL', 'INFO'),
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'file_path': str(self.BASE_DIR / 'logs' / 'app.log'),
            'max_bytes': int(os.getenv('LOG_MAX_BYTES', 10 * 1024 * 1024)),  # 10MB
            'backup_count': int(os.getenv('LOG_BACKUP_COUNT', 5))
        }
        
        # 性能配置
        self.PERFORMANCE_CONFIG = {
            'max_concurrent_tasks': int(os.getenv('MAX_CONCURRENT_TASKS', 2)),
            'task_timeout': int(os.getenv('TASK_TIMEOUT', 3600)),  # 1小时
            'cleanup_interval': int(os.getenv('CLEANUP_INTERVAL', 86400)),  # 24小时
            'max_storage_days': int(os.getenv('MAX_STORAGE_DAYS', 7))  # 7天
        }
        
        # GPU 配置
        self.GPU_CONFIG = {
            'device': os.getenv('CUDA_DEVICE', 'cuda:0'),
            'memory_fraction': float(os.getenv('GPU_MEMORY_FRACTION', 0.8)),
            'allow_growth': os.getenv('GPU_ALLOW_GROWTH', 'True').lower() == 'true'
        }
        
        # 外部工具路径
        self.TOOLS_CONFIG = {
            'colmap_path': os.getenv('COLMAP_PATH', 'colmap'),
            'ffmpeg_path': os.getenv('FFMPEG_PATH', 'ffmpeg'),
            'blender_path': os.getenv('BLENDER_PATH', 'blender'),
            'meshlab_path': os.getenv('MESHLAB_PATH', 'meshlab')
        }
        
        # 确保必要的文件夹存在
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            self.UPLOAD_FOLDER,
            self.OUTPUT_FOLDER,
            self.TEMP_FOLDER,
            str(self.BASE_DIR / 'logs')
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def get_nerf_config(self, method='nerfacto'):
        """获取特定NeRF方法的配置"""
        config = self.NERF_CONFIG.copy()
        config['method'] = method
        
        # 根据不同方法调整配置
        if method == 'instant-ngp':
            config['max_num_iterations'] = 35000
        elif method == 'mipnerf':
            config['max_num_iterations'] = 250000
        
        return config
    
    def get_colmap_config(self, quality='high'):
        """获取COLMAP配置"""
        config = self.COLMAP_CONFIG.copy()
        config['quality'] = quality
        
        # 根据质量调整参数
        if quality == 'low':
            config['feature_type'] = 'sift'
            config['matcher_type'] = 'sequential'
        elif quality == 'extreme':
            config['feature_type'] = 'sift'
            config['matcher_type'] = 'exhaustive'
        
        return config
    
    def to_dict(self):
        """将配置转换为字典"""
        return {
            'host': self.HOST,
            'port': self.PORT,
            'debug': self.DEBUG,
            'upload_folder': self.UPLOAD_FOLDER,
            'output_folder': self.OUTPUT_FOLDER,
            'max_file_size': self.MAX_FILE_SIZE,
            'max_files_per_task': self.MAX_FILES_PER_TASK,
            'nerf_config': self.NERF_CONFIG,
            'gaussian_splatting_config': self.GAUSSIAN_SPLATTING_CONFIG,
            'colmap_config': self.COLMAP_CONFIG,
            'conversion_config': self.CONVERSION_CONFIG,
            'render_config': self.RENDER_CONFIG,
            'performance_config': self.PERFORMANCE_CONFIG,
            'gpu_config': self.GPU_CONFIG,
            'tools_config': self.TOOLS_CONFIG
        }