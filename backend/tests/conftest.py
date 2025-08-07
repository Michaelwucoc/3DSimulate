import pytest
import tempfile
import shutil
import os
from pathlib import Path

# 添加项目根目录到Python路径
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import create_app
from utils.config import Config


@pytest.fixture
def app():
    """创建测试应用实例"""
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    
    # 设置测试环境变量
    test_config = {
        'TESTING': True,
        'DEBUG': False,
        'UPLOAD_FOLDER': os.path.join(temp_dir, 'uploads'),
        'OUTPUT_FOLDER': os.path.join(temp_dir, 'outputs'),
        'TEMP_FOLDER': os.path.join(temp_dir, 'temp'),
        'LOG_FOLDER': os.path.join(temp_dir, 'logs'),
        'MAX_FILE_SIZE': 1024 * 1024,  # 1MB for testing
        'MAX_FILES_PER_TASK': 10,
        'DEV_MOCK_RECONSTRUCTION': True  # 使用模拟重建
    }
    
    # 设置环境变量
    for key, value in test_config.items():
        os.environ[key] = str(value)
    
    # 创建应用
    app = create_app()
    app.config.update(test_config)
    
    # 创建必要的目录
    for folder in ['uploads', 'outputs', 'temp', 'logs']:
        os.makedirs(os.path.join(temp_dir, folder), exist_ok=True)
    
    yield app
    
    # 清理临时目录
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """创建CLI测试运行器"""
    return app.test_cli_runner()


@pytest.fixture
def sample_video_file():
    """创建示例视频文件"""
    # 创建一个小的测试文件
    temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
    temp_file.write(b'fake video content for testing')
    temp_file.close()
    
    yield temp_file.name
    
    # 清理文件
    try:
        os.unlink(temp_file.name)
    except FileNotFoundError:
        pass


@pytest.fixture
def sample_image_file():
    """创建示例图像文件"""
    temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
    temp_file.write(b'fake image content for testing')
    temp_file.close()
    
    yield temp_file.name
    
    # 清理文件
    try:
        os.unlink(temp_file.name)
    except FileNotFoundError:
        pass


@pytest.fixture
def sample_task_data():
    """示例任务数据"""
    return {
        'method': '3dgs',
        'files': ['test_video.mp4'],
        'config': {
            'iterations': 1000,
            'resolution': 512
        }
    }


class MockReconstructionService:
    """模拟重建服务"""
    
    @staticmethod
    def process_nerf_task(task):
        """模拟NeRF处理"""
        task.status = 'processing'
        task.progress = 50
        # 模拟处理完成
        task.status = 'completed'
        task.progress = 100
        return True
    
    @staticmethod
    def process_3dgs_task(task):
        """模拟3DGS处理"""
        task.status = 'processing'
        task.progress = 50
        # 模拟处理完成
        task.status = 'completed'
        task.progress = 100
        return True


@pytest.fixture
def mock_reconstruction_service(monkeypatch):
    """模拟重建服务"""
    import services.reconstruction_service
    
    monkeypatch.setattr(
        services.reconstruction_service.ReconstructionService,
        'process_nerf_task',
        MockReconstructionService.process_nerf_task
    )
    
    monkeypatch.setattr(
        services.reconstruction_service.ReconstructionService,
        'process_3dgs_task',
        MockReconstructionService.process_3dgs_task
    )
    
    return MockReconstructionService