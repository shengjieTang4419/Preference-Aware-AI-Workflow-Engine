# CrewAI Web - 统一启动脚本

.PHONY: install frontend backend dev build

# 安装依赖
install:
	cd frontend && npm install

# 启动后端
backend:
	uv run python main.py

# 启动前端（开发模式）
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
