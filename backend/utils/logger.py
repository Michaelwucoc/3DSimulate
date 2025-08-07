import logging
import logging.handlers
import os
from pathlib import Path
from datetime import datetime

def setup_logger(name='3d_reconstruction', config=None):
    """设置日志记录器"""
    
    # 默认配置
    if config is None:
        base_dir = Path(__file__).parent.parent
        log_dir = base_dir / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        config = {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'file_path': str(log_dir / 'app.log'),
            'max_bytes': 10 * 1024 * 1024,  # 10MB
            'backup_count': 5
        }
    
    # 创建日志记录器
    logger = logging.getLogger(name)
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 设置日志级别
    level = getattr(logging, config['level'].upper(), logging.INFO)
    logger.setLevel(level)
    
    # 创建格式化器
    formatter = logging.Formatter(config['format'])
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器（带轮转）
    file_handler = logging.handlers.RotatingFileHandler(
        config['file_path'],
        maxBytes=config['max_bytes'],
        backupCount=config['backup_count'],
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

class TaskLogger:
    """任务专用日志记录器"""
    
    def __init__(self, task_id: str, base_logger=None):
        self.task_id = task_id
        self.base_logger = base_logger or setup_logger()
        
        # 创建任务专用日志文件
        base_dir = Path(__file__).parent.parent
        task_log_dir = base_dir / 'logs' / 'tasks'
        task_log_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_file = task_log_dir / f'{task_id}.log'
        
        # 创建任务专用处理器
        self.task_handler = logging.FileHandler(
            self.log_file,
            encoding='utf-8'
        )
        
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        self.task_handler.setFormatter(formatter)
        
        # 创建任务日志记录器
        self.logger = logging.getLogger(f'task_{task_id}')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(self.task_handler)
        
        # 避免传播到根日志记录器
        self.logger.propagate = False
    
    def info(self, message: str):
        """记录信息日志"""
        self.logger.info(message)
        self.base_logger.info(f"[Task {self.task_id}] {message}")
    
    def warning(self, message: str):
        """记录警告日志"""
        self.logger.warning(message)
        self.base_logger.warning(f"[Task {self.task_id}] {message}")
    
    def error(self, message: str):
        """记录错误日志"""
        self.logger.error(message)
        self.base_logger.error(f"[Task {self.task_id}] {message}")
    
    def debug(self, message: str):
        """记录调试日志"""
        self.logger.debug(message)
        self.base_logger.debug(f"[Task {self.task_id}] {message}")
    
    def log_progress(self, progress: int, message: str = ''):
        """记录进度日志"""
        progress_msg = f"Progress: {progress}%"
        if message:
            progress_msg += f" - {message}"
        
        self.info(progress_msg)
    
    def log_step(self, step_name: str, status: str = 'started'):
        """记录步骤日志"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.info(f"[{timestamp}] Step '{step_name}' {status}")
    
    def log_command(self, command: str, output: str = None, error: str = None):
        """记录命令执行日志"""
        self.info(f"Executing command: {command}")
        
        if output:
            self.info(f"Command output: {output}")
        
        if error:
            self.error(f"Command error: {error}")
    
    def log_file_operation(self, operation: str, file_path: str, success: bool = True):
        """记录文件操作日志"""
        status = 'success' if success else 'failed'
        self.info(f"File {operation} {status}: {file_path}")
    
    def close(self):
        """关闭日志处理器"""
        if self.task_handler:
            self.task_handler.close()
            self.logger.removeHandler(self.task_handler)
    
    def get_log_content(self, lines: int = None):
        """获取日志内容"""
        try:
            if not self.log_file.exists():
                return ''
            
            with open(self.log_file, 'r', encoding='utf-8') as f:
                if lines is None:
                    return f.read()
                else:
                    # 读取最后几行
                    all_lines = f.readlines()
                    return ''.join(all_lines[-lines:] if len(all_lines) > lines else all_lines)
        
        except Exception as e:
            self.base_logger.error(f"Failed to read log file: {str(e)}")
            return ''

class PerformanceLogger:
    """性能监控日志记录器"""
    
    def __init__(self, logger=None):
        self.logger = logger or setup_logger('performance')
        self.start_times = {}
    
    def start_timer(self, operation: str):
        """开始计时"""
        self.start_times[operation] = datetime.now()
        self.logger.info(f"Started: {operation}")
    
    def end_timer(self, operation: str):
        """结束计时"""
        if operation not in self.start_times:
            self.logger.warning(f"No start time found for operation: {operation}")
            return
        
        start_time = self.start_times[operation]
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        self.logger.info(f"Completed: {operation} (Duration: {duration:.2f}s)")
        
        # 清理
        del self.start_times[operation]
        
        return duration
    
    def log_memory_usage(self, operation: str = None):
        """记录内存使用情况"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            memory_mb = memory_info.rss / 1024 / 1024
            
            message = f"Memory usage: {memory_mb:.2f} MB"
            if operation:
                message = f"[{operation}] {message}"
            
            self.logger.info(message)
            
        except ImportError:
            self.logger.warning("psutil not available for memory monitoring")
        except Exception as e:
            self.logger.error(f"Failed to get memory usage: {str(e)}")
    
    def log_gpu_usage(self):
        """记录GPU使用情况"""
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            
            for i, gpu in enumerate(gpus):
                self.logger.info(
                    f"GPU {i}: {gpu.name} - "
                    f"Memory: {gpu.memoryUsed}MB/{gpu.memoryTotal}MB "
                    f"({gpu.memoryUtil*100:.1f}%) - "
                    f"Load: {gpu.load*100:.1f}%"
                )
        
        except ImportError:
            self.logger.warning("GPUtil not available for GPU monitoring")
        except Exception as e:
            self.logger.error(f"Failed to get GPU usage: {str(e)}")

# 全局日志记录器实例
_global_logger = None

def get_logger(name='3d_reconstruction'):
    """获取全局日志记录器"""
    global _global_logger
    if _global_logger is None:
        _global_logger = setup_logger(name)
    return _global_logger