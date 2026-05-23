from fastapi import APIRouter, HTTPException, Depends

from crewai_web.web.api.deps import get_current_user
from crewai_web.web.domain.auth import RegisterRequest, LoginRequest, TokenResponse
from crewai_web.web.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest):
    """用户注册"""
    try:
        return await auth_service.register_user(req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    """用户登录"""
    try:
        return await auth_service.login_user(req)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/me")
async def get_me(user=Depends(get_current_user)):
    """获取当前登录用户信息"""
    return user
