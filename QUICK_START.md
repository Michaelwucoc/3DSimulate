# 3D场景重建平台 - 快速开始

## 🚀 快速启动

### 方法1: 使用启动脚本（推荐）
```bash
./start.sh
```

### 方法2: 手动启动

#### 1. 启动后端
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

#### 2. 启动前端
```bash
cd frontend
npm install
npm run dev
```

## 📱 访问平台

- **前端界面**: http://localhost:5173
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

## 🎯 使用步骤

1. **上传文件**: 在首页上传视频或图片文件
2. **开始重建**: 点击"开始3D重建"按钮
3. **查看进度**: 在"重建任务"页面查看处理进度
4. **查看结果**: 重建完成后在"3D查看器"中查看结果

## 🔧 功能特性

### 前端功能
- ✅ 文件上传界面（支持拖拽）
- ✅ 3D场景实时渲染
- ✅ 相机控制（旋转、缩放、平移）
- ✅ 测量工具
- ✅ 标注工具
- ✅ 任务进度监控

### 后端功能
- ✅ 文件上传和存储
- ✅ 3D重建任务管理
- ✅ NeRF/3DGS重建算法
- ✅ 异步任务处理
- ✅ RESTful API

## 📁 项目结构

```
3DSimulate/
├── frontend/          # React前端应用
│   ├── src/
│   │   ├── components/    # UI组件
│   │   ├── hooks/         # 自定义Hooks
│   │   └── types/         # TypeScript类型
│   └── package.json
├── backend/           # FastAPI后端服务
│   ├── app/
│   │   ├── api/          # API路由
│   │   ├── models/       # 数据库模型
│   │   ├── services/     # 业务逻辑
│   │   └── schemas/      # 数据模式
│   └── requirements.txt
├── models/            # 3D模型存储
├── uploads/           # 上传文件存储
└── start.sh          # 启动脚本
```

## 🛠️ 技术栈

### 前端
- **React 18** + **TypeScript**
- **Three.js** + **@react-three/fiber** (3D渲染)
- **Tailwind CSS** (样式)
- **Vite** (构建工具)

### 后端
- **FastAPI** (Web框架)
- **SQLAlchemy** (数据库ORM)
- **SQLite** (数据库)
- **Pillow** + **OpenCV** (图像处理)

### 3D重建
- **NeRF** (神经辐射场)
- **3D Gaussian Splatting** (3D高斯溅射)

## 🔍 开发说明

### 当前状态
- ✅ 基础UI界面完成
- ✅ 文件上传功能完成
- ✅ 3D场景渲染完成
- ✅ 后端API完成
- ⏳ 3D重建算法集成（模拟实现）
- ⏳ 真实NeRF/3DGS集成

### 下一步计划
1. 集成真实的NeRF实现（如Nerfstudio）
2. 集成3D Gaussian Splatting
3. 优化3D渲染性能
4. 添加更多测量和标注功能
5. 支持更多文件格式

## 🐛 故障排除

### 常见问题

1. **端口被占用**
   ```bash
   # 查找占用端口的进程
   lsof -i :8000  # 后端端口
   lsof -i :5173  # 前端端口
   ```

2. **依赖安装失败**
   ```bash
   # 清理缓存重新安装
   npm cache clean --force
   pip cache purge
   ```

3. **数据库错误**
   ```bash
   # 删除数据库文件重新创建
   rm backend/3d_reconstruction.db
   ```

## 📞 支持

如有问题，请查看：
- API文档: http://localhost:8000/docs
- 控制台日志
- 浏览器开发者工具 