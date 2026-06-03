"""制品Skill执行记录服务

管理 artifact_skill_executions 表的 CRUD。
"""

import logging
from typing import List, Optional
from datetime import datetime

from crewai_web.web.database import get_pool
from crewai_web.web.domain.artifact import (
    ArtifactSkillExecCreate,
    ArtifactSkillExecUpdate,
    ArtifactSkillExecOut,
)

logger = logging.getLogger(__name__)


async def create_exec_record(req: ArtifactSkillExecCreate) -> ArtifactSkillExecOut:
    """创建Skill执行记录"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO artifact_skill_executions
               (execution_id, skill_name, step_index, status)
               VALUES ($1, $2, $3, 'pending')
               RETURNING *""",
            req.execution_id, req.skill_name, req.step_index,
        )
    return ArtifactSkillExecOut(**dict(row))


async def update_exec_record(
    record_id: int, update: ArtifactSkillExecUpdate
) -> Optional[ArtifactSkillExecOut]:
    """更新Skill执行记录"""
    updates = {}
    if update.status is not None:
        updates["status"] = update.status
    if update.input_summary is not None:
        updates["input_summary"] = update.input_summary
    if update.output_files is not None:
        updates["output_files"] = update.output_files
    if update.output_metadata is not None:
        updates["output_metadata"] = update.output_metadata
    if update.error_message is not None:
        updates["error_message"] = update.error_message
    if update.started_at is not None:
        updates["started_at"] = update.started_at
    if update.completed_at is not None:
        updates["completed_at"] = update.completed_at

    if not updates:
        return await get_exec_record(record_id)

    set_clause = ", ".join(f"{k} = ${i+2}" for i, k in enumerate(updates.keys()))
    values = [record_id] + list(updates.values())

    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            f"UPDATE artifact_skill_executions SET {set_clause} WHERE id = $1 RETURNING *",
            *values,
        )
    if not row:
        return None
    return ArtifactSkillExecOut(**dict(row))


async def get_exec_record(record_id: int) -> Optional[ArtifactSkillExecOut]:
    """获取单条记录"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM artifact_skill_executions WHERE id = $1", record_id
        )
    if not row:
        return None
    return ArtifactSkillExecOut(**dict(row))


async def list_exec_records(execution_id: str) -> List[ArtifactSkillExecOut]:
    """获取某次执行的所有Skill记录"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT * FROM artifact_skill_executions
               WHERE execution_id = $1 ORDER BY step_index""",
            execution_id,
        )
    return [ArtifactSkillExecOut(**dict(r)) for r in rows]
