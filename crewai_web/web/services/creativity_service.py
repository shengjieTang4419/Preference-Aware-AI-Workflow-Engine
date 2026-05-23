"""创作服务 — 纯业务逻辑层

负责协调策略执行与数据库记录。
"""

import logging
import uuid
from datetime import datetime
from typing import Optional

from crewai_web.web.database import get_pool
from crewai_web.web.domain.creativity import (
    CreativityExecuteRequest,
    CreativityExecuteResponse,
    ArtifactOut,
)
from crewai_web.web.services.creativity import get_strategy, CreativeContext

logger = logging.getLogger(__name__)


async def execute_creative_task(
    req: CreativityExecuteRequest,
    user_id: Optional[int] = None,
) -> CreativityExecuteResponse:
    """执行创作任务

    1. 生成 execution_id 并在数据库创建记录
    2. 调用对应策略执行创作
    3. 更新数据库记录
    """
    execution_id = uuid.uuid4().hex[:12]

    # 1. 创建数据库记录（状态: running）
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO creative_artifacts
               (execution_id, user_id, scene_id, title, description, output_type, status)
               VALUES ($1, $2, $3, $4, $5, $6, 'running')
               RETURNING *""",
            execution_id, user_id, req.scene_id,
            "生成中...", "", "markdown",
        )

    logger.info(f"[创作服务] 开始执行: execution_id={execution_id}, scene={req.scene_id}")

    # 2. 调用策略
    try:
        strategy = get_strategy(req.scene_id)
        context = CreativeContext(
            scene_id=req.scene_id,
            user_input=req.input_text,
            input_files=req.input_files,
            user_id=user_id,
        )
        artifact = await strategy.execute(context)

        # 3. 更新记录为 completed
        file_names = [str(f) for f in artifact.files]
        output_dir = str(artifact.files[0].parent) if artifact.files else ""

        async with pool.acquire() as conn:
            await conn.execute(
                """UPDATE creative_artifacts
                   SET title = $2, description = $3, output_type = $4,
                       output_dir = $5, output_files = $6, preview_text = $7,
                       status = 'completed', completed_at = $8
                   WHERE execution_id = $1""",
                execution_id,
                artifact.title,
                artifact.description,
                artifact.output_type,
                output_dir,
                file_names,
                artifact.preview_text,
                datetime.utcnow(),
            )

        logger.info(f"[创作服务] 执行完成: execution_id={execution_id}")

        return CreativityExecuteResponse(
            execution_id=execution_id,
            status="completed",
            artifact=ArtifactOut(
                id=row["id"],
                execution_id=execution_id,
                user_id=user_id,
                scene_id=req.scene_id,
                title=artifact.title,
                description=artifact.description,
                output_type=artifact.output_type,
                output_dir=output_dir,
                output_files=file_names,
                preview_text=artifact.preview_text,
                status="completed",
                created_at=row["created_at"],
                completed_at=datetime.utcnow(),
            ),
        )

    except Exception as e:
        logger.error(f"[创作服务] 执行失败: execution_id={execution_id}, error={e}")
        # 更新记录为 failed
        async with pool.acquire() as conn:
            await conn.execute(
                """UPDATE creative_artifacts
                   SET status = 'failed', error_message = $2, completed_at = $3
                   WHERE execution_id = $1""",
                execution_id, str(e), datetime.utcnow(),
            )

        return CreativityExecuteResponse(
            execution_id=execution_id,
            status="failed",
        )


async def get_artifact_by_execution_id(execution_id: str) -> Optional[ArtifactOut]:
    """根据 execution_id 获取制品详情"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM creative_artifacts WHERE execution_id = $1",
            execution_id,
        )
    if not row:
        return None
    return ArtifactOut(**dict(row))
