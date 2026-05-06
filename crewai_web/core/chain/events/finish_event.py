"""
FinishEvent - 完成事件

责任链收尾节点，负责：
1. 保存执行结果到文件
2. 生成 README.md
3. 保存 metadata
4. 汇总指标
5. 触发偏好进化（如果执行成功）
"""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Optional

from crewai_web.core.chain.events.base_event import BaseEvent, EventType, ExecutionContext
from crewai_web.core.chain.events.domain import ExecutionMetadata
from crewai_web.core.chain.events.templates import generate_readme
from crewai_web.web.services.preferences_evolution_service import get_preferences_evolution_service

logger = logging.getLogger(__name__)


class FinishEvent(BaseEvent):
    """完成事件 - 汇总记录"""

    def __init__(self):
        super().__init__(EventType.STANDARD)

    def handle(self, ctx: ExecutionContext) -> ExecutionContext:
        ctx.log("INFO", "[Finish] Starting post-execution processing")

        if not ctx.output_dir:
            ctx.log("WARNING", "[Finish] No output_dir specified, skipping file output")
            return ctx

        output_path = Path(ctx.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 1. 保存执行结果
        self._save_result(ctx, output_path)

        # 2. 生成 README.md
        self._generate_readme(ctx, output_path)

        # 3. 保存 metadata
        self._save_metadata(ctx, output_path)

        # 4. 保存日志
        self._save_logs(ctx, output_path)

        # 5. 触发偏好进化（如果执行成功）
        if ctx.success:
            self._trigger_preference_evolution(ctx)

        ctx.log("INFO", "[Finish] ✅ Post-execution processing completed")

        return ctx

    def _save_result(self, ctx: ExecutionContext, output_path: Path) -> None:
        """保存执行结果到文件"""
        if ctx.result:
            (output_path / "result.txt").write_text(ctx.result, encoding="utf-8")
            ctx.log("INFO", f"[Finish] Result saved ({len(ctx.result)} chars)")

    def _generate_readme(self, ctx: ExecutionContext, output_path: Path) -> None:
        """生成 README.md"""
        readme = generate_readme(
            exec_id=ctx.exec_id,
            requirement=ctx.requirement,
            crew_name=ctx.crew_config.name if ctx.crew_config else ctx.crew_id,
            status="COMPLETED" if ctx.success else "FAILED",
            duration=ctx.duration_seconds,
            output_dir=ctx.output_dir,
            metrics=ctx.metrics,
            result=ctx.result,
        )

        (output_path / "README.md").write_text(readme, encoding="utf-8")
        ctx.log("INFO", "[Finish] README.md generated")

    def _save_metadata(self, ctx: ExecutionContext, output_path: Path) -> None:
        """保存 metadata"""
        metadata = ExecutionMetadata(
            execution_id=ctx.exec_id,
            requirement=ctx.requirement,
            crew_id=ctx.crew_id,
            process_type=ctx.crew_config.process_type if ctx.crew_config else "unknown",
            success=ctx.success,
            completed_at=str(time.time()),
            duration_seconds=ctx.duration_seconds,
            input_folder=ctx.input_folder,
            metrics=ctx.metrics,
        )

        (output_path / ".metadata.json").write_text(
            json.dumps(metadata.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
        )
        ctx.log("INFO", "[Finish] Metadata saved")

    def _save_logs(self, ctx: ExecutionContext, output_path: Path) -> None:
        """保存日志"""
        (output_path / "chain.log").write_text("\n".join(ctx.logs), encoding="utf-8")

    def _trigger_preference_evolution(self, ctx: ExecutionContext) -> None:
        """触发偏好进化（异步后台任务）"""
        try:
            evolution_service = get_preferences_evolution_service()

            # 创建后台任务生成提案（不阻塞主流程）
            asyncio.create_task(
                self._run_evolution(
                    evolution_service,
                    exec_id=ctx.exec_id,
                    exec_topic=ctx.crew_config.name if ctx.crew_config else ctx.crew_id,
                    requirement=ctx.requirement,
                    crew_config=ctx.crew_config,
                    agents_config=ctx.agent_configs,
                    tasks_config=ctx.task_configs,
                    execution_result=ctx.result,
                    user_interventions=ctx.extras.get("user_interventions", []),
                )
            )

            ctx.log("INFO", f"[Finish] Scheduled preference evolution for execution {ctx.exec_id}")

        except Exception as e:
            # 偏好进化失败不应影响主流程
            logger.error(f"[Finish] Failed to schedule evolution: {e}")

    async def _run_evolution(
        self,
        service,
        exec_id: str,
        exec_topic: str,
        requirement: str,
        crew_config,
        agents_config,
        tasks_config,
        execution_result: str,
        user_interventions: list,
    ):
        """后台生成偏好进化提案"""
        try:
            logger.info(f"[Evolution] Generating proposal for execution {exec_id}...")

            proposal = await service.generate_proposal(
                exec_id=exec_id,
                exec_topic=exec_topic,
                requirement=requirement,
                crew_config=crew_config,
                agents_config=agents_config,
                tasks_config=tasks_config,
                execution_result=execution_result,
                user_interventions=user_interventions,
            )

            logger.info(f"[Evolution] Proposal generated: {len(proposal.suggestions)} suggestions")
            logger.info(f"[Evolution] View at: /api/preferences/proposals/{exec_id}")

        except Exception as e:
            logger.error(f"[Evolution] Failed to generate proposal: {e}")
