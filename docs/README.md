# 3D 场景重建与可视化平台 - 文档总览

本项目是一个基于 Flask 后端与 React 前端的 3D 场景重建与可视化平台，支持任务管理、文件上传、结果查看与（可选）深度可视化等能力。

本文件汇总了开发环境准备、启动方式、可选依赖、环境变量、常见问题与故障排除等信息，帮助你快速上手与稳定运行。

---

## 1. 目录结构（关键部分）

- 后端（Flask）：<mcfile name="app.py" path="/Users/wujian/Documents/3DSimulate/backend/app.py"></mcfile>（应用入口，工厂函数 create_app）
- 后端运行脚本：<mcfile name="run.py" path="/Users/wujian/Documents/3DSimulate/backend/run.py"></mcfile>（支持 dev / prod / test 三种模式）
- 后端配置：<mcfile name="config.py" path="/Users/wujian/Documents/3DSimulate/backend/utils/config.py"></mcfile>
- 一键启动脚本：<mcfile name="start.sh" path="/Users/wujian/Documents/3DSimulate/start.sh"></mcfile>
- 可选深度依赖清单（如果你需要深度分析/可视化）：/Users/wujian/Documents/3DSimulate/requirements_depth.txt

---

## 2. 环境要求

- 必需：
  - Python 3.8+（推荐 3.10+）
  - Node.js 18+ 与 npm（用于前端）
- 可选（增强特性与更好体验）：
  - GPU（CUDA）
  - 可选工具：COLMAP、FFmpeg、Blender、Meshlab（部分流程或格式转换时使用）

> 后端会在启动时对 COLMAP / FFmpeg 等外部依赖进行检查并提示，但非必须。

---

## 3. 快速启动（推荐）

使用项目根目录的一键启动脚本：

```bash
cd /Users/wujian/Documents/3DSimulate
chmod +x ./start.sh      # 首次使用需要赋予可执行权限
./start.sh               # 启动前后端（默认）
```

可选参数：
- 仅启动后端：`./start.sh --backend-only`
- 仅启动前端：`./start.sh --frontend-only`

可用环境变量：
- 指定后端端口：`PORT=8010 ./start.sh`
- 指定前端端口：`FRONTEND_PORT=5174 ./start.sh`

脚本行为：
- 自动创建并激活后端虚拟环境（backend/venv）
- 安装后端依赖（backend/requirements.txt）
- 尝试安装可选依赖（requirements-optional.txt 若存在）
- 启动后端（开发模式）并做健康检查（/api/health）
- 启动前端（Vite dev server）
- Ctrl+C 可优雅关闭前后端进程

> 注：仓库中目前没有 requirements-optional.txt。如果需要深度/可视化增强依赖，请参考下文“可选依赖安装”。

---

## 4. 手动启动（备选方案）

- 启动后端（开发模式）：
  ```bash
  cd /Users/wujian/Documents/3DSimulate/backend
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  python run.py dev
  ```
- 启动前端：
  ```bash
  cd /Users/wujian/Documents/3DSimulate/frontend
  npm install
  npm run dev
  ```

访问地址：
- 前端：http://localhost:5173 （或 FRONTEND_PORT）
- 后端：http://localhost:8000 （或 PORT）
- 健康检查：http://localhost:8000/api/health

---

## 5. 后端运行模式与说明

<mcfile name="run.py" path="/Users/wujian/Documents/3DSimulate/backend/run.py"></mcfile> 提供三个模式：

- 开发模式：`python run.py dev`
  - 开启调试与热重载
  - 会执行依赖检查与 GPU 检测并打印提示
- 生产模式：`python run.py prod`
  - 优先使用 Gunicorn（若未安装则回退至 Flask 内置服务器）
- 测试模式：`python run.py test`
  - 运行 tests 目录下的测试并生成覆盖率报告

可选参数（部分）：`--host`、`--port`、`--check-deps`、`--setup`、`--log-level`

---

## 6. 配置项与环境变量

后端配置集中在 <mcfile name="config.py" path="/Users/wujian/Documents/3DSimulate/backend/utils/config.py"></mcfile>，支持通过环境变量覆盖，常用项：

- HOST（默认 0.0.0.0）
- PORT（默认 8000）
- DEBUG（默认 True）
- UPLOAD_FOLDER、OUTPUT_FOLDER、TEMP_FOLDER（默认在 backend 目录下）
- MAX_FILE_SIZE（默认 500MB）、MAX_FILES_PER_TASK（默认 100）
- NERF_VIEWER_PORT（默认 7007）等

如需覆盖，可在启动前导出环境变量，或在 shell 中内联：
```bash
PORT=8010 HOST=127.0.0.1 python backend/run.py dev
```

---

## 7. 深度可视化/分析（可选）

项目支持一个可视化端点用于基于深度结果的 Viser 交互展示，相关路由已在 <mcfile name="app.py" path="/Users/wujian/Documents/3DSimulate/backend/app.py"></mcfile> 中实现（如 `/api/depth/tasks/<task_id>/viser`）。要启用这类功能，需要安装额外依赖，例如：viser、Open3D、scenepic、transformers、depth-pro 等。

安装方式（建议在 backend/venv 环境中）：

```bash
# 进入后端虚拟环境
cd /Users/wujian/Documents/3DSimulate/backend
source venv/bin/activate

# 方式 A：使用仓库提供的额外依赖清单（如适配你的平台）
pip install -r ../requirements_depth.txt

# 方式 B：按需单独安装（示例）
pip install viser open3d scenepic transformers
# 其他库请根据实际功能需要安装
```

说明：
- 未安装这些可选依赖时，后端会输出警告，但基础 API（上传、任务、文件服务等）不受影响。
- 只有在需要运行深度可视化/分析功能时，才需要安装这些库。

---

## 8. 常用 API（节选）

- 健康检查：`GET /api/health`
- （示例）任务结果文件服务：`GET /api/depth/tasks/<task_id>/files/<path:filename>`
- 深度可视化启动：`POST /api/depth/tasks/<task_id>/viser`（可选依赖需就绪）

> 实际 API 以 <mcfile name="app.py" path="/Users/wujian/Documents/3DSimulate/backend/app.py"></mcfile> 为准，前端页面已集成主要流程。

---

## 9. 故障排除与提示

- 端口占用：修改 `PORT` 或 `FRONTEND_PORT` 环境变量重新启动。
- 可选依赖未安装的告警：如不需要相关功能可忽略；需要可视化/深度分析时按第 7 节安装。
- macOS 无 /proc：一键脚本已做兼容，Ctrl+C 可正常关闭子进程。
- 外部工具缺失（COLMAP/FFmpeg/Blender 等）：仅在使用对应功能时需要安装，参考各工具官网或包管理器安装。

---

## 10. 命令速查

- 一键启动：`./start.sh`
- 仅后端：`./start.sh --backend-only`
- 仅前端：`./start.sh --frontend-only`
- 后端开发模式：`python backend/run.py dev`
- 后端生产模式：`python backend/run.py prod`
- 后端测试模式：`python backend/run.py test`
- 健康检查：`curl http://localhost:8000/api/health`

---

如需将本总览拆分成更细的文档（例如 API 文档、部署指南、深度可视化指南等），告诉我你的偏好，我可以按需在 docs/ 下继续完善并分类整理。