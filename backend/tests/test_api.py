import pytest
import json
import io
from unittest.mock import patch, MagicMock


class TestHealthAPI:
    """健康检查API测试"""
    
    def test_health_check(self, client):
        """测试健康检查端点"""
        response = client.get('/api/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
        assert 'version' in data


class TestUploadAPI:
    """文件上传API测试"""
    
    def test_upload_single_file(self, client, sample_video_file):
        """测试单文件上传"""
        with open(sample_video_file, 'rb') as f:
            data = {
                'files': (f, 'test_video.mp4'),
                'method': '3dgs'
            }
            response = client.post('/api/upload', 
                                 data=data,
                                 content_type='multipart/form-data')
        
        assert response.status_code == 200
        
        result = json.loads(response.data)
        assert result['success'] is True
        assert 'task_id' in result
        assert 'files' in result
        assert len(result['files']) == 1
    
    def test_upload_multiple_files(self, client, sample_video_file, sample_image_file):
        """测试多文件上传"""
        with open(sample_video_file, 'rb') as f1, open(sample_image_file, 'rb') as f2:
            data = {
                'files': [(f1, 'test_video.mp4'), (f2, 'test_image.jpg')],
                'method': 'nerf'
            }
            response = client.post('/api/upload',
                                 data=data,
                                 content_type='multipart/form-data')
        
        assert response.status_code == 200
        
        result = json.loads(response.data)
        assert result['success'] is True
        assert len(result['files']) == 2
    
    def test_upload_no_files(self, client):
        """测试无文件上传"""
        data = {'method': '3dgs'}
        response = client.post('/api/upload',
                             data=data,
                             content_type='multipart/form-data')
        
        assert response.status_code == 400
        
        result = json.loads(response.data)
        assert result['success'] is False
        assert 'error' in result
    
    def test_upload_invalid_method(self, client, sample_video_file):
        """测试无效的重建方法"""
        with open(sample_video_file, 'rb') as f:
            data = {
                'files': (f, 'test_video.mp4'),
                'method': 'invalid_method'
            }
            response = client.post('/api/upload',
                                 data=data,
                                 content_type='multipart/form-data')
        
        assert response.status_code == 400
        
        result = json.loads(response.data)
        assert result['success'] is False
    
    def test_upload_large_file(self, client):
        """测试大文件上传"""
        # 创建超过限制的大文件
        large_content = b'x' * (2 * 1024 * 1024)  # 2MB，超过测试限制1MB
        
        data = {
            'files': (io.BytesIO(large_content), 'large_file.mp4'),
            'method': '3dgs'
        }
        response = client.post('/api/upload',
                             data=data,
                             content_type='multipart/form-data')
        
        assert response.status_code == 400
        
        result = json.loads(response.data)
        assert result['success'] is False
        assert 'too large' in result['error'].lower()


class TestTaskAPI:
    """任务管理API测试"""
    
    def test_get_all_tasks_empty(self, client):
        """测试获取空任务列表"""
        response = client.get('/api/tasks')
        assert response.status_code == 200
        
        result = json.loads(response.data)
        assert result['success'] is True
        assert result['tasks'] == []
    
    def test_get_task_status_not_found(self, client):
        """测试获取不存在任务的状态"""
        response = client.get('/api/tasks/nonexistent-task-id/status')
        assert response.status_code == 404
        
        result = json.loads(response.data)
        assert result['success'] is False
    
    def test_start_task_not_found(self, client):
        """测试启动不存在的任务"""
        response = client.post('/api/tasks/nonexistent-task-id/start')
        assert response.status_code == 404
        
        result = json.loads(response.data)
        assert result['success'] is False
    
    def test_delete_task_not_found(self, client):
        """测试删除不存在的任务"""
        response = client.delete('/api/tasks/nonexistent-task-id')
        assert response.status_code == 404
        
        result = json.loads(response.data)
        assert result['success'] is False


class TestIntegratedWorkflow:
    """集成工作流测试"""
    
    def test_complete_workflow(self, client, sample_video_file, mock_reconstruction_service):
        """测试完整的工作流程：上传 -> 启动 -> 检查状态 -> 获取结果"""
        # 1. 上传文件
        with open(sample_video_file, 'rb') as f:
            data = {
                'files': (f, 'test_video.mp4'),
                'method': '3dgs'
            }
            upload_response = client.post('/api/upload',
                                        data=data,
                                        content_type='multipart/form-data')
        
        assert upload_response.status_code == 200
        upload_result = json.loads(upload_response.data)
        task_id = upload_result['task_id']
        
        # 2. 启动任务
        start_response = client.post(f'/api/tasks/{task_id}/start')
        assert start_response.status_code == 200
        
        start_result = json.loads(start_response.data)
        assert start_result['success'] is True
        
        # 3. 检查任务状态
        status_response = client.get(f'/api/tasks/{task_id}/status')
        assert status_response.status_code == 200
        
        status_result = json.loads(status_response.data)
        assert status_result['success'] is True
        assert 'status' in status_result
        assert 'progress' in status_result
        
        # 4. 获取任务列表
        tasks_response = client.get('/api/tasks')
        assert tasks_response.status_code == 200
        
        tasks_result = json.loads(tasks_response.data)
        assert tasks_result['success'] is True
        assert len(tasks_result['tasks']) == 1
        assert tasks_result['tasks'][0]['id'] == task_id
        
        # 5. 删除任务
        delete_response = client.delete(f'/api/tasks/{task_id}')
        assert delete_response.status_code == 200
        
        delete_result = json.loads(delete_response.data)
        assert delete_result['success'] is True
        
        # 6. 验证任务已删除
        final_tasks_response = client.get('/api/tasks')
        final_tasks_result = json.loads(final_tasks_response.data)
        assert len(final_tasks_result['tasks']) == 0


class TestErrorHandling:
    """错误处理测试"""
    
    def test_invalid_json_request(self, client):
        """测试无效JSON请求"""
        response = client.post('/api/tasks/test-id/start',
                             data='invalid json',
                             content_type='application/json')
        
        # 应该能够处理无效JSON而不崩溃
        assert response.status_code in [400, 404]  # 可能是400（无效JSON）或404（任务不存在）
    
    def test_unsupported_method(self, client):
        """测试不支持的HTTP方法"""
        response = client.patch('/api/health')
        assert response.status_code == 405  # Method Not Allowed
    
    def test_nonexistent_endpoint(self, client):
        """测试不存在的端点"""
        response = client.get('/api/nonexistent')
        assert response.status_code == 404


class TestCORS:
    """CORS测试"""
    
    def test_cors_preflight(self, client):
        """测试CORS预检请求"""
        response = client.options('/api/health',
                                headers={
                                    'Origin': 'http://localhost:3000',
                                    'Access-Control-Request-Method': 'GET'
                                })
        
        # 检查CORS头是否存在
        assert 'Access-Control-Allow-Origin' in response.headers
    
    def test_cors_actual_request(self, client):
        """测试实际的CORS请求"""
        response = client.get('/api/health',
                            headers={'Origin': 'http://localhost:3000'})
        
        assert response.status_code == 200
        assert 'Access-Control-Allow-Origin' in response.headers


class TestRateLimiting:
    """速率限制测试（如果实现了的话）"""
    
    @pytest.mark.skip(reason="Rate limiting not implemented yet")
    def test_rate_limiting(self, client):
        """测试速率限制"""
        # 快速发送多个请求
        responses = []
        for _ in range(100):
            response = client.get('/api/health')
            responses.append(response)
        
        # 检查是否有请求被限制
        status_codes = [r.status_code for r in responses]
        assert 429 in status_codes  # Too Many Requests


class TestSecurity:
    """安全测试"""
    
    def test_sql_injection_attempt(self, client):
        """测试SQL注入尝试"""
        malicious_task_id = "'; DROP TABLE tasks; --"
        response = client.get(f'/api/tasks/{malicious_task_id}/status')
        
        # 应该安全地处理，返回404而不是500
        assert response.status_code == 404
    
    def test_path_traversal_attempt(self, client):
        """测试路径遍历尝试"""
        malicious_task_id = "../../../etc/passwd"
        response = client.get(f'/api/tasks/{malicious_task_id}/status')
        
        # 应该安全地处理
        assert response.status_code == 404
    
    def test_xss_attempt(self, client, sample_video_file):
        """测试XSS尝试"""
        with open(sample_video_file, 'rb') as f:
            data = {
                'files': (f, '<script>alert("xss")</script>.mp4'),
                'method': '3dgs'
            }
            response = client.post('/api/upload',
                                 data=data,
                                 content_type='multipart/form-data')
        
        # 应该安全地处理文件名
        if response.status_code == 200:
            result = json.loads(response.data)
            # 文件名应该被清理或拒绝
            assert '<script>' not in str(result)