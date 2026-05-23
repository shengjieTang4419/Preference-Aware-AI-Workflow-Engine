import logging
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
import jwt

from crewai_web.web.config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_HOURS
from crewai_web.web.database import get_pool
from crewai_web.web.domain.auth import RegisterRequest, LoginRequest, TokenResponse, UserInfo

logger = logging.getLogger(__name__)


# ── 密码工具 ──────────────────────────────────────────

def _hash_password(password: str) -> str:
    """密码哈希"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, hashed: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


# ── JWT 工具 ──────────────────────────────────────────

def _create_token(user_id: int, username: str) -> str:
    """生成 JWT Token"""
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS)
    payload = {"sub": str(user_id), "username": username, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _decode_token(token: str) -> dict:
    """解析 JWT Token"""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise ValueError("Token 已过期")
    except jwt.InvalidTokenError:
        raise ValueError("无效的 Token")


# ── 业务函数 ──────────────────────────────────────────

async def register_user(req: RegisterRequest) -> TokenResponse:
    """用户注册"""
    if not JWT_SECRET:
        raise ValueError("JWT_SECRET 未配置，请在 .env 中设置")

    pool = await get_pool()
    async with pool.acquire() as conn:
        existing = await conn.fetchrow("SELECT id FROM users WHERE username = $1", req.username)
        if existing:
            raise ValueError("用户名已存在")

        existing_email = await conn.fetchrow("SELECT id FROM users WHERE email = $1", req.email)
        if existing_email:
            raise ValueError("邮箱已被注册")

        password_hash = _hash_password(req.password)
        user = await conn.fetchrow(
            "INSERT INTO users (username, email, password_hash) VALUES ($1, $2, $3) "
            "RETURNING id, username, email, created_at, virtual_money",
            req.username, req.email, password_hash,
        )

    token = _create_token(user["id"], user["username"])
    logger.info(f"用户注册成功: {req.username}")
    return TokenResponse(
        access_token=token,
        user=UserInfo(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            created_at=user["created_at"].isoformat(),
        ).model_dump(),
    )


async def login_user(req: LoginRequest) -> TokenResponse:
    """用户登录"""
    if not JWT_SECRET:
        raise ValueError("JWT_SECRET 未配置，请在 .env 中设置")

    pool = await get_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT id, username, email, password_hash, created_at, virtual_money FROM users WHERE username = $1",
            req.username,
        )

    if not user or not _verify_password(req.password, user["password_hash"]):
        raise ValueError("用户名或密码错误")

    token = _create_token(user["id"], user["username"])
    logger.info(f"用户登录成功: {req.username}")
    return TokenResponse(
        access_token=token,
        user={
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "created_at": user["created_at"].isoformat(),
            "virtual_money": float(user["virtual_money"] or 0),
        },
    )


async def get_user_by_token(authorization: Optional[str]) -> dict:
    """从 Authorization header 解析当前用户"""
    if not authorization or not authorization.startswith("Bearer "):
        raise ValueError("未登录")

    token = authorization.split(" ", 1)[1]
    payload = _decode_token(token)
    user_id = int(payload["sub"])

    pool = await get_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT id, username, email, created_at, virtual_money FROM users WHERE id = $1", user_id
        )

    if not user:
        raise ValueError("用户不存在")
    result = dict(user)
    result["virtual_money"] = float(result.get("virtual_money") or 0)
    return result