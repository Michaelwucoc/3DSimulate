#!/usr/bin/env bash
set -Eeuo pipefail

# 3D场景重建平台 一键启动脚本（开发模式）
# 用法：
#   ./start.sh                # 启动前后端（默认）
#   ./start.sh --backend-only # 仅启动后端
#   ./start.sh --frontend-only# 仅启动前端

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
BACKEND_PORT="${PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

ARG_BACKEND_ONLY=false
ARG_FRONTEND_ONLY=false

for arg in "$@"; do
  case "$arg" in
    --backend-only) ARG_BACKEND_ONLY=true ;;
    --frontend-only) ARG_FRONTEND_ONLY=true ;;
    *) echo "未知参数: $arg"; exit 2 ;;
  esac
done

if [[ "$ARG_BACKEND_ONLY" == true && "$ARG_FRONTEND_ONLY" == true ]]; then
  echo "❌ 不能同时使用 --backend-only 和 --frontend-only"; exit 2
fi

log() { echo -e "$1"; }
ok() { log "✓ $1"; }
warn() { log "⚠ $1"; }
err() { log "❌ $1"; }
step() { log "\n$1"; }

check_cmd() { command -v "$1" >/dev/null 2>&1; }

wait_for_http() {
  local url="$1"; local name="$2"; local timeout="${3:-30}"; local waited=0
  if ! check_cmd curl; then warn "未检测到 curl，跳过健康检查"; return 0; fi
  until curl -sSf "$url" >/dev/null; do
    sleep 1; waited=$((waited+1))
    if [[ $waited -ge $timeout ]]; then
      warn "$name 启动可能较慢或端口被占用（超时${timeout}s），继续..."
      return 0
    fi
  done
  ok "$name 已就绪: $url"
}

BACKEND_PID=""; FRONTEND_PID=""
cleanup() {
  echo "\n🛑 正在停止服务..."
  [[ -n "$FRONTEND_PID" && -e /proc/$FRONTEND_PID ]] && kill "$FRONTEND_PID" 2>/dev/null || true
  [[ -n "$BACKEND_PID" && -e /proc/$BACKEND_PID ]] && kill "$BACKEND_PID" 2>/dev/null || true
  # macOS 没有 /proc，使用 kill -0 探测
  [[ -n "$FRONTEND_PID" ]] && kill -0 "$FRONTEND_PID" 2>/dev/null && kill "$FRONTEND_PID" 2>/dev/null || true
  [[ -n "$BACKEND_PID" ]] && kill -0 "$BACKEND_PID" 2>/dev/null && kill "$BACKEND_PID" 2>/dev/null || true
  echo "👋 已退出"
}
trap cleanup INT TERM

step "🚀 启动3D场景重建平台（开发模式）"

# -------- 检查基础环境 --------
if ! check_cmd python3; then err "Python3 未安装，请先安装"; exit 1; fi
if ! $ARG_BACKEND_ONLY; then
  if ! check_cmd node || ! check_cmd npm; then warn "Node.js/NPM 未安装，将跳过前端"; ARG_FRONTEND_ONLY=true; fi
fi

# -------- 启动后端 --------
if ! $ARG_FRONTEND_ONLY; then
  step "📦 启动后端服务..."
  cd "$BACKEND_DIR"
  # 准备虚拟环境
  if [[ ! -d venv ]]; then
    python3 -m venv venv
  fi
  # shellcheck disable=SC1091
  source venv/bin/activate
  python -m pip install --upgrade pip
  if [[ -f requirements.txt ]]; then
    pip install -r requirements.txt
  else
    warn "未找到 backend/requirements.txt，跳过依赖安装"
  fi
  # 可选依赖（存在时自动安装）
  if [[ -f requirements-optional.txt ]]; then
    step "📥 安装可选依赖（用于深度可视化/分析）..."
    pip install -r requirements-optional.txt || warn "可选依赖安装失败，可稍后手动安装"
  else
    warn "未找到 requirements-optional.txt，可选依赖（如 viser、Open3D、scenepic 等）未自动安装"
  fi

  # 以开发模式启动
  python run.py dev &
  BACKEND_PID=$!
  cd "$ROOT_DIR"
  wait_for_http "http://localhost:${BACKEND_PORT}/api/health" "后端健康检查"
fi

# -------- 启动前端 --------
if ! $ARG_BACKEND_ONLY; then
  step "🌐 启动前端服务..."
  cd "$FRONTEND_DIR"
  if [[ -f package-lock.json ]]; then
    npm ci
  else
    npm install
  fi
  npm run dev -- --port "$FRONTEND_PORT" &
  FRONTEND_PID=$!
  cd "$ROOT_DIR"
fi

step "✅ 平台启动完成！"
if ! $ARG_BACKEND_ONLY; then
  echo "📱 前端地址: http://localhost:${FRONTEND_PORT}"
fi
if ! $ARG_FRONTEND_ONLY; then
  echo "🔧 后端地址: http://localhost:${BACKEND_PORT}"
  echo "📚 API文档: http://localhost:${BACKEND_PORT}/docs"
fi

echo -e "\n按 Ctrl+C 停止服务"
wait