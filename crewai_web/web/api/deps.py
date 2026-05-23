"""API 层共享依赖

提供认证相关的 FastAPI 依赖注入函数，避免各路由文件重复实现。
"""
from typing import Optional

from fastapi import Header, HTTPException

from crewai_web.web.services import auth_service


async def get_optional_user_id(authorization: Optional[str] = Header(None)) -> Optional[int]:
    """尝试解析当前用户 ID（未登录返回 None）"""
    if not authorization:
        return None
    try:
        user = await auth_service.get_user_by_token(authorization)
        return user["id"]
    except ValueError:
        return None


async def get_required_user_id(authorization: Optional[str] = Header(None)) -> int:
    """解析当前用户 ID（未登录抛 401）"""
    if not authorization:
        raise HTTPException(status_code=401, detail="未登录")
    try:
        user = await auth_service.get_user_by_token(authorization)
        return user["id"]
    except ValueError:
        raise HTTPException(status_code=401, detail="登录已过期")


async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """解析当前用户信息（未登录抛 401）"""
    try:
        return await auth_service.get_user_by_token(authorization)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
