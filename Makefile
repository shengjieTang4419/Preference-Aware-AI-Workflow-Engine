# CrewAI Web - 创意工坊 启动脚本

.PHONY: install frontend backend dev build docker-up docker-down docker-build

# ── 本地开发 ──────────────────────────────────────

# 安装依赖
install:
	cd frontend && npm install

# 启动后端
backend:
	uv run python main.py

# 启动前端
frontend:
	cd frontend && npm run dev

# 同时启动前后端（需要两个终端）
dev:
	@echo "请开两个终端分别运行:"
	@echo "  Terminal 1: make backend"
	@echo "  Terminal 2: make frontend"

# 构建前端
build:
	cd frontend && npm run build

# ── Docker 部署 ──────────────────────────────────

# 启动所有服务
docker-up:
	docker compose up -d

# 停止所有服务
docker-down:
	docker compose down

# 构建镜像
docker-build:
	docker compose build

# 查看日志
docker-logs:
	docker compose logs -f

# 重建并启动（代码变更后）
docker-restart:
	docker compose up -d --build
