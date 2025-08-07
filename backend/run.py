#!/usr/bin/env python3
"""
3D重建后端服务启动脚本

这个脚本提供了多种启动模式：
- 开发模式：启用调试和热重载
- 生产模式：优化性能配置
- 测试模式：用于单元测试
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app import create_app
from utils.config import Config
from utils.logger import setup_logger


def setup_directories():
    """创建必要的目录"""
    config = Config()
    directories = [
        config.UPLOAD_FOLDER,
        config.OUTPUT_FOLDER,
        config.TEMP_FOLDER,
        config.LOG_FOLDER,
        os.path.join(config.OUTPUT_FOLDER, 'models'),
        os.path.join(config.OUTPUT_FOLDER, 'thumbnails'),
        os.path.join(config.OUTPUT_FOLDER, 'metadata')
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ 目录已创建: {directory}")


def check_dependencies():
    """检查系统依赖"""
    import subprocess
    
    dependencies = {
        'colmap': 'COLMAP (用于相机姿态估计)',
        'ffmpeg': 'FFmpeg (用于视频处理)'
    }
    
    missing_deps = []
    
    for cmd, desc in dependencies.items():
        try:
            subprocess.run([cmd, '--version'], 
                         capture_output=True, check=True)
            print(f"✓ {desc} 已安装")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"⚠ {desc} 未找到")
            missing_deps.append(cmd)
    
    if missing_deps:
        print("\n警告: 以下依赖未安装，可能影响某些功能:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\n请参考 README.md 安装说明")
    
    return len(missing_deps) == 0


def check_gpu():
    """检查GPU可用性"""
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        if gpus:
            for gpu in gpus:
                print(f"✓ GPU {gpu.id}: {gpu.name} (内存: {gpu.memoryTotal}MB)")
            return True
        else:
            print("⚠ 未检测到GPU，将使用CPU模式")
            return False
    except ImportError:
        print("⚠ GPUtil未安装，无法检测GPU")
        return False


def run_development():
    """开发模式启动"""
    print("🚀 启动开发服务器...")
    
    # 设置开发环境变量
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = '1'
    
    # 创建应用
    app = create_app()
    
    # 获取配置
    config = Config()
    
    # 启动服务器
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=True,
        threaded=True,
        use_reloader=True
    )


def run_production():
    """生产模式启动"""
    print("🏭 启动生产服务器...")
    
    try:
        import gunicorn.app.wsgiapp as wsgi
        
        # 设置生产环境变量
        os.environ['FLASK_ENV'] = 'production'
        os.environ['FLASK_DEBUG'] = '0'
        
        config = Config()
        
        # Gunicorn配置
        sys.argv = [
            'gunicorn',
            '--bind', f'{config.HOST}:{config.PORT}',
            '--workers', '4',
            '--worker-class', 'sync',
            '--worker-connections', '1000',
            '--max-requests', '1000',
            '--max-requests-jitter', '100',
            '--timeout', '300',
            '--keep-alive', '5',
            '--log-level', 'info',
            '--access-logfile', os.path.join(config.LOG_FOLDER, 'access.log'),
            '--error-logfile', os.path.join(config.LOG_FOLDER, 'error.log'),
            'app:create_app()'
        ]
        
        wsgi.run()
        
    except ImportError:
        print("⚠ Gunicorn未安装，使用Flask内置服务器")
        print("生产环境建议安装: pip install gunicorn")
        
        # 回退到Flask内置服务器
        os.environ['FLASK_ENV'] = 'production'
        os.environ['FLASK_DEBUG'] = '0'
        
        app = create_app()
        config = Config()
        
        app.run(
            host=config.HOST,
            port=config.PORT,
            debug=False,
            threaded=True
        )


def run_test():
    """测试模式启动"""
    print("🧪 启动测试模式...")
    
    # 设置测试环境变量
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['FLASK_DEBUG'] = '0'
    
    # 运行测试
    import pytest
    
    test_args = [
        'tests/',
        '-v',
        '--cov=.',
        '--cov-report=html',
        '--cov-report=term-missing'
    ]
    
    return pytest.main(test_args)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='3D重建后端服务启动脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python run.py dev                    # 开发模式
  python run.py prod                   # 生产模式
  python run.py test                   # 测试模式
  python run.py --check-deps           # 检查依赖
  python run.py --setup                # 初始化设置
        """
    )
    
    parser.add_argument(
        'mode',
        nargs='?',
        choices=['dev', 'prod', 'test'],
        default='dev',
        help='启动模式 (默认: dev)'
    )
    
    parser.add_argument(
        '--check-deps',
        action='store_true',
        help='检查系统依赖'
    )
    
    parser.add_argument(
        '--setup',
        action='store_true',
        help='初始化设置（创建目录等）'
    )
    
    parser.add_argument(
        '--host',
        default=None,
        help='服务器主机地址'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=None,
        help='服务器端口'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='日志级别'
    )
    
    args = parser.parse_args()
    
    # 设置日志级别
    logging.basicConfig(level=getattr(logging, args.log_level))
    
    # 覆盖配置
    if args.host:
        os.environ['HOST'] = args.host
    if args.port:
        os.environ['PORT'] = str(args.port)
    
    print("=" * 60)
    print("🎯 3D重建后端服务")
    print("=" * 60)
    
    # 初始化设置
    if args.setup or args.mode in ['dev', 'prod']:
        print("\n📁 初始化目录结构...")
        setup_directories()
    
    # 检查依赖
    if args.check_deps or args.mode in ['dev', 'prod']:
        print("\n🔍 检查系统依赖...")
        check_dependencies()
        
        print("\n🖥️ 检查GPU可用性...")
        check_gpu()
    
    if args.check_deps:
        return
    
    if args.setup:
        print("\n✅ 初始化完成！")
        return
    
    print(f"\n🚀 启动模式: {args.mode.upper()}")
    print("-" * 60)
    
    # 根据模式启动服务
    try:
        if args.mode == 'dev':
            run_development()
        elif args.mode == 'prod':
            run_production()
        elif args.mode == 'test':
            exit_code = run_test()
            sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n👋 服务已停止")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()