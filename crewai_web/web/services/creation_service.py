import logging
from typing import List, Optional
from datetime import datetime

from crewai_web.web.database import get_pool
from crewai_web.web.domain.creation import CreationCreate, CreationOut

logger = logging.getLogger(__name__)


async def create_creation(req: CreationCreate, user_id: Optional[int] = None) -> CreationOut:
    """创建创作记录"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO creations (user_id, scene_id, input_text, input_files, status)
               VALUES ($1, $2, $3, $4, 'pending')
               RETURNING *""",
            user_id, req.scene_id, req.input_text, req.input_files,
        )
    logger.info(f"创作记录已创建: scene={req.scene_id}")
    return CreationOut(**dict(row))


async def list_creations(user_id: Optional[int] = None, limit: int = 20) -> List[CreationOut]:
    """获取创作记录列表"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        if user_id:
            rows = await conn.fetch(
                "SELECT * FROM creations WHERE user_id = $1 ORDER BY created_at DESC LIMIT $2",
                user_id, limit,
            )
        else:
            rows = await conn.fetch(
                "SELECT * FROM creations ORDER BY created_at DESC LIMIT $1", limit
            )
    return [CreationOut(**dict(r)) for r in rows]


async def get_creation(creation_id: int) -> Optional[CreationOut]:
    """获取单个创作记录"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM creations WHERE id = $1", creation_id)
    if not row:
        return None
    return CreationOut(**dict(row))


async def update_creation_status(creation_id: int, status: str,
                                  output_dir: Optional[str] = None,
                                  output_files: Optional[list] = None,
                                  error_message: Optional[str] = None,
                                  execution_id: Optional[str] = None) -> Optional[CreationOut]:
    """更新创作状态"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        completed_at = datetime.utcnow() if status in ('completed', 'failed') else None
        row = await conn.fetchrow(
            """UPDATE creations
               SET status = $2, output_dir = $3, output_files = $4,
                   error_message = $5, execution_id = $6, completed_at = $7
               WHERE id = $1 RETURNING *""",
            creation_id, status, output_dir, output_files, error_message, execution_id, completed_at,
        )
    if not row:
        return None
    return CreationOut(**dict(row))
