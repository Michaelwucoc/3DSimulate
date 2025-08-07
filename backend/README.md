# 3D重建后端服务

这是一个基于Flask的3D重建后端服务，支持NeRF和3D Gaussian Splatting等重建算法。

## 功能特性

- 🎥 **多格式文件上传**: 支持视频和图像文件上传
- 🔄 **多种重建算法**: 支持NeRF、3D Gaussian Splatting等
- 📊 **实时进度跟踪**: 提供详细的任务进度和状态信息
- 🔧 **模型格式转换**: 支持多种3D模型格式导出
- 📈 **性能监控**: 内置性能监控和日志记录
- 🎨 **缩略图生成**: 自动生成模型预览缩略图

## 项目结构

```
backend/
├── app.py                 # 主应用入口
├── requirements.txt       # Python依赖
├── README.md             # 项目文档
├── models/               # 数据模型
│   └── task.py          # 任务模型定义
├── services/            # 业务服务
│   ├── file_service.py      # 文件处理服务
│   ├── reconstruction_service.py  # 重建服务
│   └── model_converter.py   # 模型转换服务
├── utils/               # 工具模块
│   ├── config.py        # 配置管理
│   └── logger.py        # 日志工具
├── uploads/             # 上传文件目录
├── outputs/             # 输出结果目录
├── temp/                # 临时文件目录
└── logs/                # 日志文件目录
```

## 安装指南

### 1. 环境要求

- Python 3.8+
- CUDA 11.0+ (可选，用于GPU加速)
- COLMAP (用于相机姿态估计)
- FFmpeg (用于视频处理)
- Blender (可选，用于模型转换)

### 2. 安装Python依赖

```bash
cd backend
pip install -r requirements.txt
```

### 3. 安装外部工具

#### COLMAP安装

**Ubuntu/Debian:**
```bash
sudo apt-get install colmap
```

**macOS:**
```bash
brew install colmap
```

**Windows:**
从 [COLMAP官网](https://colmap.github.io/) 下载预编译版本

#### FFmpeg安装

**Ubuntu/Debian:**
```bash
sudo apt-get install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
从 [FFmpeg官网](https://ffmpeg.org/) 下载预编译版本

### 4. 环境配置

创建 `.env` 文件（可选）：

```bash
# 服务器配置
HOST=0.0.0.0
PORT=8000
DEBUG=True

# 文件存储
UPLOAD_FOLDER=./uploads
OUTPUT_FOLDER=./outputs
TEMP_FOLDER=./temp

# 文件大小限制（字节）
MAX_FILE_SIZE=524288000  # 500MB
MAX_FILES_PER_TASK=100

# NeRF配置
NERF_MAX_ITERATIONS=30000
NERF_VIEWER_PORT=7007

# 3D Gaussian Splatting配置
GS_ITERATIONS=30000
GS_RESOLUTION=-1

# COLMAP配置
COLMAP_THREADS=-1

# GPU配置
CUDA_DEVICE=cuda:0
GPU_MEMORY_FRACTION=0.8

# 工具路径
COLMAP_PATH=colmap
FFMPEG_PATH=ffmpeg
BLENDER_PATH=blender

# 日志配置
LOG_LEVEL=INFO
LOG_MAX_BYTES=10485760  # 10MB
LOG_BACKUP_COUNT=5

# 性能配置
MAX_CONCURRENT_TASKS=2
TASK_TIMEOUT=3600  # 1小时
CLEANUP_INTERVAL=86400  # 24小时
MAX_STORAGE_DAYS=7  # 7天
```

## 使用方法

### 1. 启动服务

```bash
cd backend
python app.py
```

服务将在 `http://localhost:8000` 启动。

### 2. API接口

#### 健康检查
```http
GET /api/health
```

#### 文件上传
```http
POST /api/upload
Content-Type: multipart/form-data

files: [文件列表]
method: nerf|3dgs  # 重建方法
```

#### 开始重建任务
```http
POST /api/tasks/{task_id}/start
```

#### 获取任务状态
```http
GET /api/tasks/{task_id}/status
```

#### 获取所有任务
```http
GET /api/tasks
```

#### 获取任务结果
```http
GET /api/tasks/{task_id}/result
```

#### 下载结果文件
```http
GET /api/tasks/{task_id}/download/{file_type}
# file_type: model|thumbnail|metadata
```

#### 删除任务
```http
DELETE /api/tasks/{task_id}
```

### 3. 使用示例

```python
import requests
import time

# 1. 上传文件
files = {'files': open('video.mp4', 'rb')}
data = {'method': '3dgs'}
response = requests.post('http://localhost:8000/api/upload', 
                        files=files, data=data)
task_id = response.json()['task_id']

# 2. 开始重建
requests.post(f'http://localhost:8000/api/tasks/{task_id}/start')

# 3. 监控进度
while True:
    response = requests.get(f'http://localhost:8000/api/tasks/{task_id}/status')
    status = response.json()
    
    print(f"状态: {status['status']}, 进度: {status['progress']}%")
    
    if status['status'] in ['completed', 'failed']:
        break
    
    time.sleep(5)

# 4. 下载结果
if status['status'] == 'completed':
    response = requests.get(f'http://localhost:8000/api/tasks/{task_id}/download/model')
    with open('result_model.ply', 'wb') as f:
        f.write(response.content)
```

## 支持的重建算法

### 1. NeRF (Neural Radiance Fields)
- **方法**: `nerf`
- **特点**: 高质量的新视角合成
- **适用**: 静态场景重建
- **输出**: 神经网络模型 + 渲染结果

### 2. 3D Gaussian Splatting
- **方法**: `3dgs`
- **特点**: 实时渲染，高效训练
- **适用**: 实时应用场景
- **输出**: 点云模型 + 高斯参数

### 3. Instant-NGP
- **方法**: `instant-ngp`
- **特点**: 快速训练，实时渲染
- **适用**: 快速原型制作
- **输出**: 优化的神经网络模型

## 支持的文件格式

### 输入格式
- **视频**: MP4, AVI, MOV, MKV, WEBM, M4V, FLV, WMV
- **图像**: JPG, JPEG, PNG, BMP, TIFF, TIF, WEBP

### 输出格式
- **点云**: PLY
- **网格**: OBJ, STL
- **现代格式**: GLTF, GLB
- **通用格式**: FBX

## 性能优化

### 1. GPU加速
- 确保安装了CUDA和相应的GPU驱动
- 在配置中设置正确的GPU设备
- 监控GPU内存使用情况

### 2. 并发处理
- 通过 `MAX_CONCURRENT_TASKS` 控制并发任务数
- 根据硬件配置调整参数

### 3. 存储管理
- 定期清理临时文件
- 设置合理的文件保留期限
- 监控磁盘空间使用

## 故障排除

### 常见问题

1. **COLMAP不可用**
   - 检查COLMAP是否正确安装
   - 验证PATH环境变量
   - 尝试手动指定COLMAP路径

2. **GPU内存不足**
   - 减少批处理大小
   - 降低图像分辨率
   - 调整GPU内存分配比例

3. **文件上传失败**
   - 检查文件大小限制
   - 验证文件格式支持
   - 确认磁盘空间充足

4. **重建任务失败**
   - 查看详细日志信息
   - 检查输入数据质量
   - 验证算法参数设置

### 日志查看

```bash
# 查看应用日志
tail -f logs/app.log

# 查看特定任务日志
tail -f logs/tasks/{task_id}.log
```

## 开发指南

### 1. 添加新的重建算法

1. 在 `services/reconstruction_service.py` 中添加新方法
2. 实现相应的数据准备和模型训练逻辑
3. 更新配置文件中的算法参数
4. 添加相应的测试用例

### 2. 扩展文件格式支持

1. 在 `services/file_service.py` 中添加格式验证
2. 在 `services/model_converter.py` 中添加转换逻辑
3. 更新支持格式列表

### 3. 性能监控

使用内置的性能监控工具：

```python
from utils.logger import PerformanceLogger

perf_logger = PerformanceLogger()
perf_logger.start_timer('operation_name')
# ... 执行操作 ...
perf_logger.end_timer('operation_name')
perf_logger.log_memory_usage('operation_name')
perf_logger.log_gpu_usage()
```

## 许可证

本项目采用 MIT 许可证。详见 LICENSE 文件。

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

如有问题，请通过以下方式联系：
- 提交 GitHub Issue
- 发送邮件至项目维护者