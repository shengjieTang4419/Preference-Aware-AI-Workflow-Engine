import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pydantic import ValidationError
from dotenv import load_dotenv

from crewai_web.web.api import api_router
from crewai_web.web.config import ensure_storage_dirs, STORAGE_DIR, ENV_FILE

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    # 加载 .env 文件
    if ENV_FILE.exists():
        load_dotenv(ENV_FILE, override=True)
        print(f"✅ Loaded environment from: {ENV_FILE}")
    else:
        print(f"⚠️  .env file not found: {ENV_FILE}")
    
    ensure_storage_dirs()
    print(f"✅ Storage directory ready: {STORAGE_DIR}")
    yield
    # 关闭时
    print("🛑 Shutting down...")


app = FastAPI(
    title="CrewAI Web Control",
    description="Web UI for managing CrewAI agents, tasks and executions",
    version="0.1.0",
    lifespan=lifespan,
)


# ── 全局异常处理器 ──────────────────────────────────

@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(status_code=422, content={"detail": f"数据验证错误: {str(exc)}"})


@app.exception_handler(TimeoutError)
async def timeout_error_handler(request: Request, exc: TimeoutError):
    logger.error(f"Timeout: {exc}")
    return JSONResponse(status_code=504, content={"detail": "AI 调用超时，请稍后重试"})


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    logger.error(f"ValueError: {exc}")
    return JSONResponse(status_code=400, content={"detail": str(exc)})


# ── 中间件 ──────────────────────────────────────────

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 路由
app.include_router(api_router, prefix="/api")

# 静态文件服务 (执行结果输出目录)
app.mount("/storage", StaticFiles(directory=STORAGE_DIR), name="storage")


@app.get("/api/health")
def health_check():
    """健康检查"""
    return {"status": "ok", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("crewai_web.web.app:app", host="0.0.0.0", port=8000, reload=True)
