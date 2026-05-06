"""
Crew 异步执行引擎 - 使用责任链模式

执行流程：
    PreHandleEvent → BusinessEventDispatcher → FinishEvent → TouchEvent
                            ↓
                    Strategy.schedule(BusinessEvents)
"""

import asyncio
import logging
import traceback
from pathlib import Path
from typing import Optional, Tuple

from crewai_web.web.services import execution_service
from crewai_web.web.domain.execution import ExecutionStatus
from crewai_web.web.runner.execution_logger import ExecutionLogger
from crewai_web.core.chain.event_chain import build_default_chain
from crewai_web.core.chain.events.base_event import ExecutionContext


logger = logging.getLogger(__name__)


def _sync_run_crew(
    exec_id: str, requirement: str, input_folder: Optional[str], crew_id: str, output_dir: str
) -> Tuple[bool, str, Optional[str]]:
    """
    同步执行 Crew - 使用责任链模式
    返回: (success, logs, error)
    """
    exec_logger = ExecutionLogger(exec_id, lambda level, msg: execution_service.append_log(exec_id, level, msg))

    try:
        exec_logger.info(f"=== Starting Execution {exec_id} ===")
        exec_logger.info(f"Requirement: {requirement[:100]}...")
        exec_logger.info(f"Crew: {crew_id}, Output: {output_dir}")

        # 更新状态
        execution_service.update_execution_status(exec_id, ExecutionStatus.RUNNING)
        exec_logger.info("Status: RUNNING")

        # 获取 inputs
        exec_meta = execution_service.get_execution(exec_id)
        inputs = getattr(exec_meta, "inputs", None) or {}
        exec_logger.info(f"Inputs: {inputs}")

        # 构建执行上下文
        exec_logger.info("Building execution context...")
        ctx = ExecutionContext(
            crew_id=crew_id,
            requirement=requirement,
            inputs=inputs,
            exec_id=exec_id,
            output_dir=output_dir,
            input_folder=input_folder,
        )

        # 构建并执行责任链
        exec_logger.info("Executing chain: PreHandle → Business → Finish → Touch")
        chain = build_default_chain()
        ctx = chain.execute(ctx)

        result_text = ctx.result or ""
        exec_logger.info(f"Execution completed! Result: {len(result_text)} chars")
        exec_logger.info("=== Execution Completed ===")

        # 更新状态
        execution_service.update_execution_status(
            exec_id,
            ExecutionStatus.COMPLETED,
            logs_summary=f"Completed {len(ctx.task_configs)} tasks. Result: {result_text[:200]}...",
        )

        return True, exec_logger.get_all_logs(), None

    except Exception as e:
        error_msg = str(e)
        exec_logger.error(f"Execution failed: {error_msg}")
        exec_logger.error(traceback.format_exc())

        execution_service.update_execution_status(
            exec_id, ExecutionStatus.FAILED, error_message=error_msg, logs_summary=f"Failed: {error_msg[:200]}"
        )

        return False, exec_logger.get_all_logs(), error_msg


async def run_crew_async(exec_id: str, requirement: str, input_folder: Optional[str], crew_id: str, output_dir: str):
    """
    异步执行 Crew (使用线程池避免阻塞事件循环)

    注意：偏好进化已在 FinishEvent 中处理，这里只负责异步调度
    """
    loop = asyncio.get_event_loop()
    success, logs, error = await loop.run_in_executor(
        None, _sync_run_crew, exec_id, requirement, input_folder, crew_id, output_dir
    )

    return success, logs, error
