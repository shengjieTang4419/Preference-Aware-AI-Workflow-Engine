"""运行 Crew 事件 — Pipeline 第 8 步 (原 ExecuteArtifactEvent 变为第 9 步)

在 Crew 配置生成完成后，自动创建执行记录并运行 Crew。
"""

import logging
from crewai_web.core.event import BusinessEvent, EventContext
from crewai_web.web.services import execution_service, crew_service
from crewai_web.web.domain.execution import ExecutionCreate, ExecutionStatus

logger = logging.getLogger(__name__)


class RunCrewEvent(BusinessEvent):
    """步骤 8: 运行 Crew"""

    name = "运行 Crew"
    step = 8
    total = 9

    async def do_execute(self, ctx: EventContext) -> None:
        if not ctx.crew_id:
            logger.warning("[RunCrew] 没有 crew_id，跳过执行")
            return

        crew = crew_service.get_crew(ctx.crew_id)
        if not crew:
            logger.error(f"[RunCrew] Crew '{ctx.crew_id}' 不存在")
            return

        # 创建执行记录
        exec_create = ExecutionCreate(
            requirement=ctx.scenario,
            crew_id=ctx.crew_id,
            output_dir="outputs",  # 相对路径，会被 execution_service 自动转为 exec_dir/outputs
        )
        exec_record = execution_service.create_execution(exec_create)
        ctx.crew_execution_id = exec_record.id
        logger.info(f"[RunCrew] 创建执行记录: {exec_record.id}")

        # 同步执行 Crew（在当前 pipeline 内完成）
        from crewai_web.web.runner.crew_runner import _sync_run_crew
        import asyncio

        loop = asyncio.get_event_loop()
        success, logs, error = await loop.run_in_executor(
            None,
            _sync_run_crew,
            exec_record.id,
            exec_record.requirement,
            exec_record.input_folder,
            exec_record.crew_id,
            exec_record.output_dir,
        )

        if success:
            # 读取执行结果
            result_text = ""
            try:
                exec_meta = execution_service.get_execution(exec_record.id)
                if exec_meta and exec_meta.logs_summary:
                    result_text = exec_meta.logs_summary
            except Exception:
                pass

            ctx.crew_output = result_text
            logger.info(f"[RunCrew] 执行成功: {len(result_text)} chars")
        else:
            logger.error(f"[RunCrew] 执行失败: {error}")
            ctx.crew_output = ""
