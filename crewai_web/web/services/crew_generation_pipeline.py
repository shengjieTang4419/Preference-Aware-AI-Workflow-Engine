"""
Crew 生成 Pipeline - 编排所有事件步骤
"""

import asyncio
import logging
from typing import Optional
from crewai_web.core.event.event_context import EventContext
from crewai_web.core.tools.execution_logger import execution_logger
from crewai_web.core.tools.websocket_manager import ws_manager
from crewai_web.web.services.chat_execution_log_service import execution_log_service
from crewai_web.web.domain.execution_log import ExecutionStatus
from crewai_web.web.events import (
    GenerateTopicEvent,
    GenerateTasksPlanEvent,
    MatchAgentsEvent,
    CreateCrewEvent,
    CreateTasksEvent,
    AssignModelsEvent,
    VerifyEvent,
)

logger = logging.getLogger(__name__)


class CrewGenerationPipeline:
    """Crew 生成 Pipeline - 组合所有事件步骤"""

    def __init__(self):
        self.events = [
            GenerateTopicEvent(),
            GenerateTasksPlanEvent(),
            MatchAgentsEvent(),
            CreateCrewEvent(),
            CreateTasksEvent(),
            AssignModelsEvent(),
            VerifyEvent(),
        ]

    async def execute(
        self,
        execution_id: str,
        scenario: str,
        doc_filenames: Optional[list[str]] = None,
    ) -> dict:
        """
        执行 Pipeline（完整流程，包含状态管理）

        Args:
            execution_id: 执行 ID
            scenario: 用户场景描述
            doc_filenames: 上传的文档文件名列表

        Returns:
            生成结果 dict
        """
        # 更新状态为运行中
        execution_log_service.update_status(execution_id, ExecutionStatus.RUNNING)

        # 等待前端 WebSocket 连接建立（避免错过进度消息）
        logger.info(f"[Pipeline] Waiting 1s for WebSocket connection...")
        await asyncio.sleep(1.0)

        ctx = EventContext(
            execution_id=execution_id,
            scenario=scenario,
            doc_filenames=doc_filenames,
        )

        logger.info(f"[Pipeline] Starting for scenario: {scenario[:100]}...")
        execution_logger.log(execution_id, "INFO", f"Pipeline 开始: {scenario[:100]}")

        try:
            for event in self.events:
                await event.execute(ctx)

            # 推送完成
            await ws_manager.send_complete(execution_id, ctx.to_result())
            execution_logger.log(execution_id, "INFO", "Pipeline 完成")
            execution_log_service.update_status(execution_id, ExecutionStatus.COMPLETED)

        except Exception as e:
            ctx.error = str(e)
            await ws_manager.send_error(execution_id, ctx.error)
            execution_logger.log(execution_id, "ERROR", f"Pipeline 失败: {ctx.error}")
            execution_log_service.update_status(execution_id, ExecutionStatus.FAILED)
            raise

        return ctx.to_result()


# 全局单例
crew_generation_pipeline = CrewGenerationPipeline()
