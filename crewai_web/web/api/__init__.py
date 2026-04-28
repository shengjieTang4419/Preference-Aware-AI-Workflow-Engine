"""API 路由聚合层

所有子路由已在定义时配置 prefix 和 tags，此处直接挂载
"""
from fastapi import APIRouter
from .agents import router as agents_router
from .tasks import router as tasks_router
from .crews import router as crews_router
from .files import router as files_router
from .executions import router as executions_router
from .chat import router as chat_router
from .skills import router as skills_router
from .execution_logs import router as execution_logs_router
from .preferences import router as preferences_router
from .llm_settings import router as llm_settings_router

api_router = APIRouter()

api_router.include_router(agents_router)
api_router.include_router(tasks_router)
api_router.include_router(crews_router)
api_router.include_router(files_router)
api_router.include_router(executions_router)
api_router.include_router(chat_router)
api_router.include_router(skills_router)
api_router.include_router(execution_logs_router)
api_router.include_router(preferences_router)
api_router.include_router(llm_settings_router)
