from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.models.database import create_tables
from app.api.v1.endpoints import upload, reconstruction
import logging

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename=settings.log_file if settings.log_file else None
)

# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="3D场景重建与可视化平台API",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")
app.mount("/models", StaticFiles(directory=settings.models_dir), name="models")

# 包含API路由
app.include_router(upload.router, prefix="/api/v1", tags=["upload"])
app.include_router(reconstruction.router, prefix="/api/v1", tags=["reconstruction"])

@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    # 创建数据库表
    create_tables()
    logging.info("应用启动完成")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理"""
    logging.info("应用关闭")

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "3D场景重建与可视化平台API",
        "version": settings.app_version,
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": settings.app_version
    }

@app.get("/api/info")
async def api_info():
    """API信息"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "3D场景重建与可视化平台API",
        "endpoints": {
            "upload": "/api/v1/upload",
            "reconstruction": "/api/v1/reconstruction",
            "docs": "/docs"
        }
    }

# 全局异常处理器
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    logging.error(f"未处理的异常: {str(exc)}")
    return HTTPException(
        status_code=500,
        detail="内部服务器错误"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    ) 