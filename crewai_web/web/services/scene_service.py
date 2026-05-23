import logging
from typing import List, Optional

from crewai_web.web.database import get_pool
from crewai_web.web.domain.scene import SceneOut

logger = logging.getLogger(__name__)


async def list_scenes(enabled_only: bool = True) -> List[SceneOut]:
    """获取场景卡片列表（从 scene_configs 读取）"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        if enabled_only:
            rows = await conn.fetch(
                "SELECT * FROM scene_configs WHERE enabled = TRUE AND visible = TRUE ORDER BY sort_order"
            )
        else:
            rows = await conn.fetch("SELECT * FROM scene_configs ORDER BY sort_order")
    return [SceneOut(**dict(r)) for r in rows]


async def get_scene(scene_id: str) -> Optional[SceneOut]:
    """获取单个场景"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM scene_configs WHERE id = $1", scene_id)
    if not row:
        return None
    return SceneOut(**dict(row))
