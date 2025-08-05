# 3D场景重建与可视化平台

一个基于NeRF和3D Gaussian Splatting的互动式3D场景重建与可视化平台。

## 功能特性

### 前端功能
- 🎥 视频和图片上传界面
- 🌐 3D场景实时渲染和交互
- 📏 测量工具和标注功能
- 🎮 流畅的相机控制（旋转、缩放、漫游）
- 📱 移动设备优化

### 后端功能
- 🤖 NeRF/3DGS模型集成
- 🔄 3D重建处理管道
- 📦 3D模型数据格式转换
- ⚡ 异步处理支持

### 技术栈
- **前端**: React + TypeScript + Three.js + Vite
- **后端**: Python + FastAPI + Celery
- **3D重建**: Nerfstudio + 3D Gaussian Splatting
- **数据库**: SQLite (开发) / PostgreSQL (生产)

## 快速开始

### 环境要求
- Python 3.8+
- Node.js 18+
- CUDA支持的GPU (推荐)

### 安装步骤

1. 克隆项目
```bash
git clone <repository-url>
cd 3DSimulate
```

2. 安装后端依赖
```bash
cd backend
pip install -r requirements.txt
```

3. 安装前端依赖
```bash
cd frontend
npm install
```

4. 启动开发服务器
```bash
# 启动后端
cd backend
uvicorn main:app --reload

# 启动前端 (新终端)
cd frontend
npm run dev
```

## 项目结构

```
3DSimulate/
├── frontend/          # React前端应用
├── backend/           # FastAPI后端服务
├── models/            # 3D重建模型和脚本
├── docs/             # 文档
└── README.md
```

## 使用指南

1. 打开浏览器访问 `http://localhost:5173`
2. 上传视频文件或图片
3. 等待3D重建处理完成
4. 在3D场景中进行交互和探索

## 开发计划

- [ ] 基础前端界面
- [ ] 文件上传功能
- [ ] 3D场景渲染
- [ ] 后端API开发
- [ ] NeRF/3DGS集成
- [ ] 性能优化
- [ ] 移动端适配
- [ ] 高级功能（测量、标注等）

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License 