#!/bin/bash

# 3D场景重建平台启动脚本

echo "🚀 启动3D场景重建平台..."

# 检查Node.js和Python是否安装
if ! command -v node &> /dev/null; then
    echo "❌ Node.js未安装，请先安装Node.js"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python3未安装，请先安装Python3"
    exit 1
fi

# 启动后端
echo "📦 启动后端服务..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py &
BACKEND_PID=$!
cd ..

# 等待后端启动
echo "⏳ 等待后端服务启动..."
sleep 5

# 启动前端
echo "🌐 启动前端服务..."
cd frontend
npm install
npm run dev &
FRONTEND_PID=$!
cd ..

echo "✅ 平台启动完成！"
echo "📱 前端地址: http://localhost:5173"
echo "🔧 后端地址: http://localhost:8000"
echo "📚 API文档: http://localhost:8000/docs"

# 等待用户中断
echo ""
echo "按 Ctrl+C 停止服务"
trap "echo '🛑 正在停止服务...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait 