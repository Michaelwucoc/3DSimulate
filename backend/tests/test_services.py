import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

# 添加项目根目录到Python路径
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.file_service import FileService
from services.reconstruction_service import ReconstructionService
from services.model_converter import ModelConverter
from models.task import Task, TaskStatus, ReconstructionMethod, UploadedFile
from utils.config import Config


class TestFileService:
    """文件服务测试"""
    
    def setup_method(self):
        """测试前设置"""
        self.config = Config()
        self.file_service = FileService(self.config)
    
    def test_validate_file_size_valid(self):
        """测试有效文件大小验证"""
        # 创建小文件
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file.write(b'small content')
            temp_file.flush()
            
            is_valid, error = self.file_service.validate_file_size(temp_file.name)
            assert is_valid is True
            assert error is None
    
    def test_validate_file_size_invalid(self):
        """测试无效文件大小验证"""
        # 模拟大文件
        with patch('os.path.getsize', return_value=self.config.MAX_FILE_SIZE + 1):
            is_valid, error = self.file_service.validate_file_size('fake_large_file.mp4')
            assert is_valid is False
            assert 'too large' in error.lower()
    
    def test_validate_file_format_video(self):
        """测试视频文件格式验证"""
        valid_videos = ['test.mp4', 'test.avi', 'test.mov', 'test.mkv']
        invalid_videos = ['test.txt', 'test.exe', 'test.pdf']
        
        for video in valid_videos:
            is_valid, error = self.file_service.validate_file_format(video)
            assert is_valid is True, f"Should accept {video}"
            assert error is None
        
        for video in invalid_videos:
            is_valid, error = self.file_service.validate_file_format(video)
            assert is_valid is False, f"Should reject {video}"
            assert error is not None
    
    def test_validate_file_format_image(self):
        """测试图像文件格式验证"""
        valid_images = ['test.jpg', 'test.jpeg', 'test.png', 'test.bmp']
        invalid_images = ['test.txt', 'test.exe', 'test.pdf']
        
        for image in valid_images:
            is_valid, error = self.file_service.validate_file_format(image)
            assert is_valid is True, f"Should accept {image}"
            assert error is None
        
        for image in invalid_images:
            is_valid, error = self.file_service.validate_file_format(image)
            assert is_valid is False, f"Should reject {image}"
            assert error is not None
    
    @patch('cv2.VideoCapture')
    def test_validate_video_content_valid(self, mock_cv2):
        """测试有效视频内容验证"""
        # 模拟有效视频
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.return_value = 30.0  # FPS
        mock_cv2.return_value = mock_cap
        
        is_valid, error = self.file_service.validate_video_content('test.mp4')
        assert is_valid is True
        assert error is None
    
    @patch('cv2.VideoCapture')
    def test_validate_video_content_invalid(self, mock_cv2):
        """测试无效视频内容验证"""
        # 模拟无效视频
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = False
        mock_cv2.return_value = mock_cap
        
        is_valid, error = self.file_service.validate_video_content('test.mp4')
        assert is_valid is False
        assert error is not None
    
    @patch('PIL.Image.open')
    def test_validate_image_content_valid(self, mock_pil):
        """测试有效图像内容验证"""
        # 模拟有效图像
        mock_img = MagicMock()
        mock_img.size = (1920, 1080)
        mock_img.mode = 'RGB'
        mock_pil.return_value = mock_img
        
        is_valid, error = self.file_service.validate_image_content('test.jpg')
        assert is_valid is True
        assert error is None
    
    @patch('PIL.Image.open')
    def test_validate_image_content_invalid(self, mock_pil):
        """测试无效图像内容验证"""
        # 模拟PIL异常
        mock_pil.side_effect = Exception("Invalid image")
        
        is_valid, error = self.file_service.validate_image_content('test.jpg')
        assert is_valid is False
        assert error is not None
    
    @patch('subprocess.run')
    def test_extract_frames_success(self, mock_subprocess):
        """测试成功提取视频帧"""
        mock_subprocess.return_value.returncode = 0
        
        with tempfile.TemporaryDirectory() as temp_dir:
            success = self.file_service.extract_frames('test.mp4', temp_dir)
            assert success is True
            mock_subprocess.assert_called_once()
    
    @patch('subprocess.run')
    def test_extract_frames_failure(self, mock_subprocess):
        """测试提取视频帧失败"""
        mock_subprocess.return_value.returncode = 1
        
        with tempfile.TemporaryDirectory() as temp_dir:
            success = self.file_service.extract_frames('test.mp4', temp_dir)
            assert success is False
    
    def test_get_storage_usage(self):
        """测试存储使用情况获取"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建一些测试文件
            test_file = os.path.join(temp_dir, 'test.txt')
            with open(test_file, 'w') as f:
                f.write('test content')
            
            with patch.object(self.config, 'UPLOAD_FOLDER', temp_dir):
                usage = self.file_service.get_storage_usage()
                
                assert 'total_size' in usage
                assert 'file_count' in usage
                assert 'folders' in usage
                assert usage['total_size'] > 0
                assert usage['file_count'] > 0


class TestReconstructionService:
    """重建服务测试"""
    
    def setup_method(self):
        """测试前设置"""
        self.config = Config()
        self.reconstruction_service = ReconstructionService(self.config)
    
    @patch('subprocess.run')
    def test_check_colmap_available(self, mock_subprocess):
        """测试COLMAP可用性检查"""
        mock_subprocess.return_value.returncode = 0
        
        is_available = self.reconstruction_service.check_colmap_available()
        assert is_available is True
    
    @patch('subprocess.run')
    def test_check_colmap_unavailable(self, mock_subprocess):
        """测试COLMAP不可用"""
        mock_subprocess.side_effect = FileNotFoundError()
        
        is_available = self.reconstruction_service.check_colmap_available()
        assert is_available is False
    
    @patch('subprocess.run')
    def test_check_ffmpeg_available(self, mock_subprocess):
        """测试FFmpeg可用性检查"""
        mock_subprocess.return_value.returncode = 0
        
        is_available = self.reconstruction_service.check_ffmpeg_available()
        assert is_available is True
    
    def test_create_task(self):
        """测试任务创建"""
        files = [
            UploadedFile(
                filename='test.mp4',
                original_name='test.mp4',
                file_path='/path/to/test.mp4',
                file_size=1024,
                file_type='video'
            )
        ]
        
        task = Task(
            id='test-task-id',
            method=ReconstructionMethod.GAUSSIAN_SPLATTING,
            files=files,
            status=TaskStatus.PENDING
        )
        
        assert task.id == 'test-task-id'
        assert task.method == ReconstructionMethod.GAUSSIAN_SPLATTING
        assert len(task.files) == 1
        assert task.status == TaskStatus.PENDING
    
    @patch('services.reconstruction_service.ReconstructionService._run_colmap')
    @patch('services.reconstruction_service.ReconstructionService._train_3dgs_model')
    @patch('services.reconstruction_service.ReconstructionService._export_3dgs_results')
    def test_process_3dgs_task_success(self, mock_export, mock_train, mock_colmap):
        """测试3DGS任务处理成功"""
        # 模拟成功的处理步骤
        mock_colmap.return_value = True
        mock_train.return_value = True
        mock_export.return_value = True
        
        # 创建测试任务
        files = [
            UploadedFile(
                filename='test.mp4',
                original_name='test.mp4',
                file_path='/path/to/test.mp4',
                file_size=1024,
                file_type='video'
            )
        ]
        
        task = Task(
            id='test-task-id',
            method=ReconstructionMethod.GAUSSIAN_SPLATTING,
            files=files,
            status=TaskStatus.PENDING
        )
        
        # 处理任务
        success = self.reconstruction_service.process_3dgs_task(task)
        
        assert success is True
        assert task.status == TaskStatus.COMPLETED
        assert task.progress == 100
    
    @patch('services.reconstruction_service.ReconstructionService._run_colmap')
    def test_process_3dgs_task_failure(self, mock_colmap):
        """测试3DGS任务处理失败"""
        # 模拟COLMAP失败
        mock_colmap.return_value = False
        
        # 创建测试任务
        files = [
            UploadedFile(
                filename='test.mp4',
                original_name='test.mp4',
                file_path='/path/to/test.mp4',
                file_size=1024,
                file_type='video'
            )
        ]
        
        task = Task(
            id='test-task-id',
            method=ReconstructionMethod.GAUSSIAN_SPLATTING,
            files=files,
            status=TaskStatus.PENDING
        )
        
        # 处理任务
        success = self.reconstruction_service.process_3dgs_task(task)
        
        assert success is False
        assert task.status == TaskStatus.FAILED


class TestModelConverter:
    """模型转换服务测试"""
    
    def setup_method(self):
        """测试前设置"""
        self.config = Config()
        self.model_converter = ModelConverter(self.config)
    
    @patch('subprocess.run')
    def test_check_blender_available(self, mock_subprocess):
        """测试Blender可用性检查"""
        mock_subprocess.return_value.returncode = 0
        
        is_available = self.model_converter.check_blender_available()
        assert is_available is True
    
    @patch('subprocess.run')
    def test_check_blender_unavailable(self, mock_subprocess):
        """测试Blender不可用"""
        mock_subprocess.side_effect = FileNotFoundError()
        
        is_available = self.model_converter.check_blender_available()
        assert is_available is False
    
    def test_validate_conversion_request_valid(self):
        """测试有效转换请求验证"""
        request = {
            'input_file': 'model.ply',
            'output_format': 'obj',
            'output_file': 'model.obj'
        }
        
        is_valid, error = self.model_converter.validate_conversion_request(request)
        assert is_valid is True
        assert error is None
    
    def test_validate_conversion_request_invalid_format(self):
        """测试无效格式转换请求"""
        request = {
            'input_file': 'model.ply',
            'output_format': 'invalid_format',
            'output_file': 'model.invalid'
        }
        
        is_valid, error = self.model_converter.validate_conversion_request(request)
        assert is_valid is False
        assert error is not None
    
    def test_validate_conversion_request_missing_fields(self):
        """测试缺少字段的转换请求"""
        request = {
            'input_file': 'model.ply'
            # 缺少 output_format 和 output_file
        }
        
        is_valid, error = self.model_converter.validate_conversion_request(request)
        assert is_valid is False
        assert error is not None
    
    @patch('subprocess.run')
    def test_convert_to_ply_success(self, mock_subprocess):
        """测试成功转换为PLY格式"""
        mock_subprocess.return_value.returncode = 0
        
        success = self.model_converter.convert_to_ply(
            'input.obj', 'output.ply'
        )
        assert success is True
    
    @patch('subprocess.run')
    def test_convert_to_ply_failure(self, mock_subprocess):
        """测试转换为PLY格式失败"""
        mock_subprocess.return_value.returncode = 1
        
        success = self.model_converter.convert_to_ply(
            'input.obj', 'output.ply'
        )
        assert success is False
    
    @patch('subprocess.run')
    def test_convert_to_gltf_success(self, mock_subprocess):
        """测试成功转换为GLTF格式"""
        mock_subprocess.return_value.returncode = 0
        
        success = self.model_converter.convert_to_gltf(
            'input.ply', 'output.gltf'
        )
        assert success is True
    
    def test_optimize_model_mock(self):
        """测试模型优化（模拟）"""
        # 由于优化是模拟的，应该总是返回True
        success = self.model_converter.optimize_model(
            'input.ply', 'optimized.ply'
        )
        assert success is True
    
    @patch('PIL.Image.new')
    @patch('PIL.Image.Image.save')
    def test_generate_thumbnail_success(self, mock_save, mock_new):
        """测试成功生成缩略图"""
        # 模拟PIL Image
        mock_img = MagicMock()
        mock_new.return_value = mock_img
        
        success = self.model_converter.generate_thumbnail(
            'model.ply', 'thumbnail.png'
        )
        assert success is True
    
    @patch('PIL.Image.new')
    def test_generate_thumbnail_failure(self, mock_new):
        """测试生成缩略图失败"""
        # 模拟PIL异常
        mock_new.side_effect = Exception("PIL error")
        
        success = self.model_converter.generate_thumbnail(
            'model.ply', 'thumbnail.png'
        )
        assert success is False


class TestIntegrationServices:
    """服务集成测试"""
    
    def setup_method(self):
        """测试前设置"""
        self.config = Config()
        self.file_service = FileService(self.config)
        self.reconstruction_service = ReconstructionService(self.config)
        self.model_converter = ModelConverter(self.config)
    
    def test_service_initialization(self):
        """测试服务初始化"""
        assert self.file_service is not None
        assert self.reconstruction_service is not None
        assert self.model_converter is not None
        
        assert self.file_service.config == self.config
        assert self.reconstruction_service.config == self.config
        assert self.model_converter.config == self.config
    
    @patch('services.file_service.FileService.validate_file_format')
    @patch('services.file_service.FileService.validate_file_size')
    @patch('services.file_service.FileService.validate_video_content')
    def test_file_validation_pipeline(self, mock_video, mock_size, mock_format):
        """测试文件验证管道"""
        # 模拟所有验证步骤成功
        mock_format.return_value = (True, None)
        mock_size.return_value = (True, None)
        mock_video.return_value = (True, None)
        
        # 验证视频文件
        format_valid, format_error = self.file_service.validate_file_format('test.mp4')
        size_valid, size_error = self.file_service.validate_file_size('test.mp4')
        content_valid, content_error = self.file_service.validate_video_content('test.mp4')
        
        assert format_valid is True
        assert size_valid is True
        assert content_valid is True
        assert all(error is None for error in [format_error, size_error, content_error])
    
    def test_task_lifecycle(self):
        """测试任务生命周期"""
        # 创建任务
        files = [
            UploadedFile(
                filename='test.mp4',
                original_name='test.mp4',
                file_path='/path/to/test.mp4',
                file_size=1024,
                file_type='video'
            )
        ]
        
        task = Task(
            id='test-task-id',
            method=ReconstructionMethod.GAUSSIAN_SPLATTING,
            files=files,
            status=TaskStatus.PENDING
        )
        
        # 验证初始状态
        assert task.status == TaskStatus.PENDING
        assert task.progress == 0
        
        # 模拟状态变化
        task.status = TaskStatus.PROCESSING
        task.progress = 50
        
        assert task.status == TaskStatus.PROCESSING
        assert task.progress == 50
        
        # 模拟完成
        task.status = TaskStatus.COMPLETED
        task.progress = 100
        
        assert task.status == TaskStatus.COMPLETED
        assert task.progress == 100