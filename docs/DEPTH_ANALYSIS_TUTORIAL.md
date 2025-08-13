# 深度分析和场景可视化教程

## 概述
本教程将指导您如何使用我们的深度分析工具，对16个相机的RGB图像、度量深度图及相机内外参进行处理。

## 功能特性
- **场景和相机可视化**: 使用 Viser、Open3D、ScenePic 三种方式可视化
- **COLMAP稀疏重建**: 生成稀疏点云并与度量深度对比
- **单目深度估计**: 支持 DepthAnything v2 和 Depth-Pro 算法
- **深度特征分析**: 区分归一化深度 vs 度量深度

## 准备工作

### 1. 安装可选依赖
```bash
# 确保位于项目根目录
cd /path/to/3DSimulate

# 方式1: 通过启动脚本自动安装 (推荐)
./start.sh --backend-only

# 方式2: 手动安装
source backend/venv/bin/activate
pip install -r backend/requirements-optional.txt

# 方式3: 单独安装核心库
pip install viser open3d scenepic transformers torch
pip install git+https://github.com/apple/depth-pro.git  # 可选

# 安装COLMAP (macOS)
brew install colmap
```

### 2. 数据格式要求
您的数据应包含以下文件：

```
your_data/
├── images/              # RGB图像目录
│   ├── image_0000.jpg
│   ├── image_0001.jpg
│   └── ... (共16个图像)
├── depths/              # 深度图目录
│   ├── depth_0000.npy   # 或 depth_0000.png
│   ├── depth_0001.npy
│   └── ... (共16个深度图)
├── intrinsics.npy       # 或 intrinsics.json
└── extrinsics.npy       # 或 extrinsics.json
```

**格式说明:**
- **RGB图像**: `.jpg`, `.png` 格式
- **深度图**: `.npy` (numpy数组) 或 `.png` (16位深度图)
- **内参**: 3x3矩阵 或字典格式 `{"camera_0": [[fx,0,cx],[0,fy,cy],[0,0,1]], ...}`
- **外参**: 4x4矩阵 (camera to world) 或字典格式

## 使用方法

### 方法1: 通过Web API (推荐)

#### 1. 启动后端服务
```bash
# 启动后端 (自动安装可选依赖)
./start.sh --backend-only

# or 手动启动
cd backend
python run.py dev
```

#### 2. 上传数据并启动分析
```bash
# 上传数据 (form-data格式)
curl -X POST http://localhost:8000/api/depth/upload \
  -F "images=@your_data/images/image_0000.jpg" \
  -F "images=@your_data/images/image_0001.jpg" \
  ... \
  -F "depths=@your_data/depths/depth_0000.npy" \
  -F "depths=@your_data/depths/depth_0001.npy" \
  ... \
  -F "intrinsics=@your_data/intrinsics.npy" \
  -F "extrinsics=@your_data/extrinsics.npy"

# 响应示例:
# {"task_id": "abc123", "message": "深度分析数据上传成功", "files_count": {"images": 16, "depths": 16}}
```

#### 3. 启动深度分析任务
```bash
# 使用返回的task_id启动分析
curl -X POST http://localhost:8000/api/depth/tasks/abc123/start \
  -H "Content-Type: application/json" \
  -d '{
    "visualization": ["open3d", "scenepic"],
    "colmap": true,
    "monocular_depth": "depthanything_v2",
    "port": 8081
  }'
```

#### 4. 检查任务状态
```bash
# 查看任务进度
curl http://localhost:8000/api/depth/tasks/abc123/status
```

#### 5. Viser实时可视化
```bash
# 启动Viser可视化服务器
curl -X POST http://localhost:8000/api/depth/tasks/abc123/viser \
  -H "Content-Type: application/json" \
  -d '{"port": 8080}'

# 然后访问: http://localhost:8080
```

#### 6. 查看结果
- **ScenePic HTML**: `http://localhost:8000/api/depth/tasks/abc123/files/scenepic_visualization.html`
- **深度特征分析图**: `http://localhost:8000/api/depth/tasks/abc123/files/depth_characteristics_analysis.png`
- **COLMAP结果**: `http://localhost:8000/api/depth/tasks/abc123/files/colmap/`

### 方法2: 直接命令行使用

```bash
# 激活虚拟环境
source backend/venv/bin/activate

# 切换到tools目录
cd tools

# 运行深度分析
python depth_analysis.py \
  --data_dir /path/to/your_data \
  --images_dir /path/to/your_data/images \
  --depth_dir /path/to/your_data/depths \
  --intrinsics /path/to/your_data/intrinsics.npy \
  --extrinsics /path/to/your_data/extrinsics.npy \
  --output_dir ./output \
  --viz all \
  --colmap \
  --monocular_depth depthanything_v2 \
  --port 8080
```

## 可视化详解

### 1. Viser 交互式可视化
- **特点**: 基于Web的实时3D交互
- **访问**: `http://localhost:8080` (可自定义端口)
- **功能**: 
  - 相机位置和朝向可视化
  - 深度点云显示
  - 实时交互控制

### 2. Open3D 桌面可视化
- **特点**: 本地桌面3D窗口
- **功能**:
  - 高质量相机frustum显示
  - 深度点云可视化
  - 鼠标交互控制

### 3. ScenePic HTML输出
- **特点**: 生成独立的HTML文件
- **优势**: 便于分享和展示
- **输出**: `output/scenepic_visualization.html`

## COLMAP处理流程

1. **特征提取**: 从RGB图像提取SIFT特征
2. **特征匹配**: 建立图像间对应关系
3. **稀疏重建**: 生成相机位姿和稀疏点云
4. **深度对比**: 将COLMAP点云与度量深度图对比

**对比可视化**: COLMAP点云(红色) vs 深度点云(蓝色)

## 单目深度估计

### DepthAnything v2
- **特点**: 基于Transformer的深度估计
- **输出**: 归一化深度图
- **模型**: `depth-anything/Depth-Anything-V2-Small-hf`

### Depth-Pro (Apple)
- **特点**: 高精度度量深度估计
- **输出**: 直接的度量深度
- **安装**: `pip install git+https://github.com/apple/depth-pro.git`

## 深度特征分析

系统会自动生成深度特征分析图，包括：
- **度量深度分布**: 原始深度值的统计分布
- **归一化深度分布**: [0,1]范围内的归一化分布
- **统计信息**: 最小值、最大值、平均值

**文件位置**: `output/depth_characteristics_analysis.png`

## 故障排除

### 1. 依赖问题
```bash
# 检查可选依赖安装状态
python -c "import viser, open3d, scenepic; print('所有可视化库已安装')"
python -c "import transformers, torch; print('深度估计库已安装')"
```

### 2. COLMAP未安装
```bash
# macOS
brew install colmap

# Ubuntu
sudo apt install colmap

# 检查安装
colmap --help
```

### 3. 端口被占用
```bash
# 检查端口使用情况
lsof -i :8080

# 使用不同端口
curl -X POST http://localhost:8000/api/depth/tasks/abc123/viser \
  -d '{"port": 8090}'
```

### 4. 内存不足
- 减少处理的相机数量
- 降低图像分辨率
- 使用更小的深度估计模型

## API参考

### 上传深度数据
```http
POST /api/depth/upload
Content-Type: multipart/form-data

Form fields:
- images: 多个RGB图像文件
- depths: 多个深度图文件  
- intrinsics: 相机内参文件
- extrinsics: 相机外参文件
```

### 启动分析任务
```http
POST /api/depth/tasks/{task_id}/start
Content-Type: application/json

{
  "visualization": ["viser", "open3d", "scenepic"], // 可选组合
  "colmap": true,                                    // 是否运行COLMAP
  "monocular_depth": "depthanything_v2",            // 或 "depth_pro"
  "port": 8081                                       // Viser端口
}
```

### 启动Viser可视化
```http
POST /api/depth/tasks/{task_id}/viser
Content-Type: application/json

{
  "port": 8080  // 可视化服务器端口
}
```

## 性能优化

- **GPU加速**: 深度估计会自动使用可用的GPU
- **并行处理**: 多相机数据并行处理
- **内存管理**: 大数据集时分批处理
- **缓存机制**: 避免重复计算

## 常见用例

1. **多视图几何验证**: 使用COLMAP验证相机标定精度
2. **深度图质量评估**: 对比度量深度与估计深度
3. **场景理解**: 通过可视化理解3D场景结构
4. **算法对比**: 比较不同深度估计算法的效果

## 输出文件说明

```
output/
├── depth_characteristics_analysis.png    # 深度特征分析图
├── scenepic_visualization.html           # ScenePic可视化
├── colmap/                               # COLMAP输出
│   ├── database.db
│   ├── images/
│   └── sparse/
├── depthanything_v2_*.npy               # 深度估计结果
└── depth_pro_*.npy                      # Depth-Pro结果
```

需要更多帮助，请查看 [API文档](http://localhost:8000/docs) 或提交issue。