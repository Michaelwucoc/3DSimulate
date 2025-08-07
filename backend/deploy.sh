#!/bin/bash

# 3D重建后端服务部署脚本
# 支持开发环境和生产环境部署

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示帮助信息
show_help() {
    cat << EOF
3D重建后端服务部署脚本

用法: $0 [选项] [环境]

环境:
    dev         开发环境部署
    prod        生产环境部署
    test        测试环境部署

选项:
    -h, --help              显示此帮助信息
    -c, --clean             清理旧的部署文件
    -i, --install-deps      安装系统依赖
    -s, --setup-env         设置环境配置
    -d, --daemon            以守护进程模式运行（仅生产环境）
    -p, --port PORT         指定端口（默认：8000）
    --host HOST             指定主机（默认：0.0.0.0）
    --workers NUM           指定工作进程数（仅生产环境，默认：4）
    --no-gpu                禁用GPU支持
    --skip-tests            跳过测试

示例:
    $0 dev                  # 开发环境部署
    $0 prod -d              # 生产环境守护进程部署
    $0 test --skip-tests    # 测试环境部署，跳过测试
    $0 dev -p 8080          # 开发环境，指定端口8080

EOF
}

# 默认配置
ENVIRONMENT="dev"
PORT="8000"
HOST="0.0.0.0"
WORKERS="4"
CLEAN=false
INSTALL_DEPS=false
SETUP_ENV=false
DAEMON=false
NO_GPU=false
SKIP_TESTS=false

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -c|--clean)
            CLEAN=true
            shift
            ;;
        -i|--install-deps)
            INSTALL_DEPS=true
            shift
            ;;
        -s|--setup-env)
            SETUP_ENV=true
            shift
            ;;
        -d|--daemon)
            DAEMON=true
            shift
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --workers)
            WORKERS="$2"
            shift 2
            ;;
        --no-gpu)
            NO_GPU=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        dev|prod|test)
            ENVIRONMENT="$1"
            shift
            ;;
        *)
            log_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 检查操作系统
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        if command -v apt-get &> /dev/null; then
            PACKAGE_MANAGER="apt"
        elif command -v yum &> /dev/null; then
            PACKAGE_MANAGER="yum"
        elif command -v dnf &> /dev/null; then
            PACKAGE_MANAGER="dnf"
        else
            log_error "不支持的Linux发行版"
            exit 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        PACKAGE_MANAGER="brew"
    else
        log_error "不支持的操作系统: $OSTYPE"
        exit 1
    fi
    
    log_info "检测到操作系统: $OS ($PACKAGE_MANAGER)"
}

# 检查Python版本
check_python() {
    log_info "检查Python版本..."
    
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3未安装"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    REQUIRED_VERSION="3.8"
    
    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
        log_success "Python版本检查通过: $PYTHON_VERSION"
    else
        log_error "Python版本过低: $PYTHON_VERSION (需要 >= $REQUIRED_VERSION)"
        exit 1
    fi
}

# 安装系统依赖
install_system_deps() {
    log_info "安装系统依赖..."
    
    case $PACKAGE_MANAGER in
        apt)
            sudo apt-get update
            sudo apt-get install -y \
                python3-pip python3-venv python3-dev \
                build-essential cmake \
                ffmpeg \
                libopencv-dev \
                colmap
            ;;
        yum|dnf)
            sudo $PACKAGE_MANAGER install -y \
                python3-pip python3-devel \
                gcc gcc-c++ cmake \
                ffmpeg ffmpeg-devel \
                opencv opencv-devel
            # COLMAP需要手动编译或使用第三方源
            log_warning "COLMAP需要手动安装"
            ;;
        brew)
            brew install python3 cmake ffmpeg opencv colmap
            ;;
    esac
    
    log_success "系统依赖安装完成"
}

# 设置Python虚拟环境
setup_venv() {
    log_info "设置Python虚拟环境..."
    
    if [[ ! -d "venv" ]]; then
        python3 -m venv venv
        log_success "虚拟环境创建完成"
    else
        log_info "虚拟环境已存在"
    fi
    
    source venv/bin/activate
    
    # 升级pip
    pip install --upgrade pip
    
    # 安装Python依赖
    log_info "安装Python依赖..."
    pip install -r requirements.txt
    
    log_success "Python依赖安装完成"
}

# 设置环境配置
setup_environment() {
    log_info "设置环境配置..."
    
    if [[ ! -f ".env" ]]; then
        cp .env.example .env
        log_info "已创建.env文件，请根据需要修改配置"
    else
        log_info ".env文件已存在"
    fi
    
    # 根据环境设置特定配置
    case $ENVIRONMENT in
        dev)
            sed -i.bak "s/DEBUG=.*/DEBUG=True/" .env
            sed -i.bak "s/FLASK_ENV=.*/FLASK_ENV=development/" .env
            ;;
        prod)
            sed -i.bak "s/DEBUG=.*/DEBUG=False/" .env
            sed -i.bak "s/FLASK_ENV=.*/FLASK_ENV=production/" .env
            ;;
        test)
            sed -i.bak "s/DEBUG=.*/DEBUG=False/" .env
            sed -i.bak "s/FLASK_ENV=.*/FLASK_ENV=testing/" .env
            ;;
    esac
    
    # 设置端口和主机
    sed -i.bak "s/PORT=.*/PORT=$PORT/" .env
    sed -i.bak "s/HOST=.*/HOST=$HOST/" .env
    
    # GPU配置
    if [[ "$NO_GPU" == "true" ]]; then
        sed -i.bak "s/CUDA_DEVICE=.*/CUDA_DEVICE=cpu/" .env
    fi
    
    # 删除备份文件
    rm -f .env.bak
    
    log_success "环境配置完成"
}

# 创建必要目录
setup_directories() {
    log_info "创建必要目录..."
    
    mkdir -p uploads outputs temp logs
    mkdir -p outputs/models outputs/thumbnails outputs/metadata
    
    log_success "目录创建完成"
}

# 运行测试
run_tests() {
    if [[ "$SKIP_TESTS" == "true" ]]; then
        log_info "跳过测试"
        return
    fi
    
    log_info "运行测试..."
    
    if [[ -f "venv/bin/activate" ]]; then
        source venv/bin/activate
    fi
    
    python -m pytest tests/ -v --tb=short
    
    if [[ $? -eq 0 ]]; then
        log_success "所有测试通过"
    else
        log_error "测试失败"
        exit 1
    fi
}

# 清理旧文件
clean_deployment() {
    if [[ "$CLEAN" == "true" ]]; then
        log_info "清理旧的部署文件..."
        
        rm -rf venv/
        rm -rf __pycache__/
        rm -rf .pytest_cache/
        rm -rf *.egg-info/
        find . -name "*.pyc" -delete
        find . -name "*.pyo" -delete
        
        log_success "清理完成"
    fi
}

# 启动服务
start_service() {
    log_info "启动$ENVIRONMENT环境服务..."
    
    if [[ -f "venv/bin/activate" ]]; then
        source venv/bin/activate
    fi
    
    case $ENVIRONMENT in
        dev)
            python run.py dev --host $HOST --port $PORT
            ;;
        prod)
            if [[ "$DAEMON" == "true" ]]; then
                nohup python run.py prod --host $HOST --port $PORT > logs/app.log 2>&1 &
                echo $! > app.pid
                log_success "服务已在后台启动 (PID: $(cat app.pid))"
                log_info "日志文件: logs/app.log"
                log_info "停止服务: kill \$(cat app.pid)"
            else
                python run.py prod --host $HOST --port $PORT
            fi
            ;;
        test)
            python run.py test
            ;;
    esac
}

# 检查服务状态
check_service() {
    log_info "检查服务状态..."
    
    if [[ -f "app.pid" ]]; then
        PID=$(cat app.pid)
        if ps -p $PID > /dev/null; then
            log_success "服务正在运行 (PID: $PID)"
        else
            log_warning "PID文件存在但进程未运行"
            rm -f app.pid
        fi
    else
        log_info "服务未在后台运行"
    fi
    
    # 检查端口
    if command -v netstat &> /dev/null; then
        if netstat -tuln | grep ":$PORT " > /dev/null; then
            log_success "端口 $PORT 正在监听"
        else
            log_info "端口 $PORT 未在监听"
        fi
    fi
}

# 主函数
main() {
    echo "======================================"
    echo "🎯 3D重建后端服务部署脚本"
    echo "======================================"
    echo "环境: $ENVIRONMENT"
    echo "主机: $HOST"
    echo "端口: $PORT"
    echo "======================================"
    
    # 检测系统
    detect_os
    
    # 检查Python
    check_python
    
    # 清理（如果需要）
    clean_deployment
    
    # 安装系统依赖（如果需要）
    if [[ "$INSTALL_DEPS" == "true" ]]; then
        install_system_deps
    fi
    
    # 设置虚拟环境
    setup_venv
    
    # 设置环境配置（如果需要）
    if [[ "$SETUP_ENV" == "true" ]]; then
        setup_environment
    fi
    
    # 创建目录
    setup_directories
    
    # 运行测试
    if [[ "$ENVIRONMENT" != "prod" ]]; then
        run_tests
    fi
    
    # 检查服务状态
    check_service
    
    echo "======================================"
    log_success "部署准备完成！"
    echo "======================================"
    
    # 启动服务
    start_service
}

# 信号处理
trap 'log_info "部署被中断"; exit 1' INT TERM

# 运行主函数
main "$@"