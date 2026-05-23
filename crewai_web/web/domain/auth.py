from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    """注册请求"""
    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    email: str = Field(..., description="邮箱")
    password: str = Field(..., min_length=6, description="密码")


class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class TokenResponse(BaseModel):
    """登录/注册响应"""
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserInfo(BaseModel):
    """用户信息"""
    id: int
    username: str
    email: str
    created_at: str
