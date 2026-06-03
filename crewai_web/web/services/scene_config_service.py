import logging
from typing import List, Optional
from datetime import datetime

from crewai_web.web.database import get_pool
from crewai_web.web.domain.scene_config import (
    SceneConfigCreate, SceneConfigUpdate, SceneConfigOut,
)

logger = logging.getLogger(__name__)


async def list_configs(enabled_only: bool = True, visible_only: bool = True) -> List[SceneConfigOut]:
    """获取场景配置列表"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        conditions = []
        if enabled_only:
            conditions.append("enabled = TRUE")
        if visible_only:
            conditions.append("visible = TRUE")
        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        rows = await conn.fetch(
            f"SELECT * FROM scene_configs {where} ORDER BY sort_order"
        )
    return [SceneConfigOut(**dict(r)) for r in rows]


async def get_config(config_id: str) -> Optional[SceneConfigOut]:
    """获取单个场景配置"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM scene_configs WHERE id = $1", config_id)
    if not row:
        return None
    return SceneConfigOut(**dict(row))


async def get_config_by_title(title: str) -> Optional[SceneConfigOut]:
    """通过 title 模糊匹配场景配置"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM scene_configs WHERE title = $1 AND enabled = TRUE LIMIT 1",
            title,
        )
    if not row:
        return None
    return SceneConfigOut(**dict(row))


async def create_config(req: SceneConfigCreate) -> SceneConfigOut:
    """创建场景配置"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        existing = await conn.fetchval("SELECT 1 FROM scene_configs WHERE id = $1", req.id)
        if existing:
            raise ValueError(f"场景配置 '{req.id}' 已存在")
        now = datetime.utcnow()
        row = await conn.fetchrow(
            """INSERT INTO scene_configs
               (id, icon, title, subtitle, placeholder, category, tags,
                output_format, enabled, visible, sort_order, price_tier,
                exec_mode, output_dir, crew_template, description, artifact_skills, created_at, updated_at)
               VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$18)
               RETURNING *""",
            req.id, req.icon, req.title, req.subtitle, req.placeholder,
            req.category, req.tags, req.output_format, req.enabled, req.visible,
            req.sort_order, req.price_tier, req.exec_mode, req.output_dir,
            req.crew_template, req.description, req.artifact_skills, now,
        )
    logger.info(f"场景配置已创建: {req.id}")
    return SceneConfigOut(**dict(row))


async def update_config(config_id: str, req: SceneConfigUpdate) -> Optional[SceneConfigOut]:
    """更新场景配置"""
    updates = {k: v for k, v in req.model_dump(exclude_unset=True).items() if v is not None}
    if not updates:
        return await get_config(config_id)

    updates["updated_at"] = datetime.utcnow()
    set_clause = ", ".join(f"{k} = ${i+2}" for i, k in enumerate(updates.keys()))
    values = [config_id] + list(updates.values())

    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            f"UPDATE scene_configs SET {set_clause} WHERE id = $1 RETURNING *", *values
        )
    if not row:
        return None
    logger.info(f"场景配置已更新: {config_id}")
    return SceneConfigOut(**dict(row))


async def delete_config(config_id: str) -> bool:
    """删除场景配置"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute("DELETE FROM scene_configs WHERE id = $1", config_id)
    return result == "DELETE 1"
