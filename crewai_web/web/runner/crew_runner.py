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

logger = logging.getLogger(__name__)


def _sync_run_crew(
    exec_id: str,
    requirement: str,
    input_folder: Optional[str],
    crew_id: str,
    output_dir: str
) -> Tuple[bool, str, Optional[str], Optional[dict]]:
    """
    同步执行 Crew - 使用责任链模式
    返回: (success, logs, error, evolution_context)
    """
    from crewai_web.core.chain.event_chain import build_default_chain
    from crewai_web.core.chain.events.base_event import ExecutionContext
    
    exec_logger = ExecutionLogger(exec_id, lambda level, msg: execution_service.append_log(exec_id, level, msg))
    evolution_context = None

    try:
        exec_logger.info(f"=== Starting Execution {exec_id} ===")
        exec_logger.info(f"Requirement: {requirement[:100]}...")
        exec_logger.info(f"Crew: {crew_id}, Output: {output_dir}")

        # 更新状态
        execution_service.update_execution_status(exec_id, ExecutionStatus.RUNNING)
        exec_logger.info("Status: RUNNING")

        # 获取 inputs
        exec_meta = execution_service.get_execution(exec_id)
        inputs = getattr(exec_meta, 'inputs', None) or {}
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

        # 构建偏好进化上下文（从 ctx.extras 获取）
        evolution_context = ctx.extras.get("evolution_context")
        if evolution_context:
            exec_logger.info("Evolution context prepared")

        exec_logger.info("=== Execution Completed ===")

        # 更新状态
        execution_service.update_execution_status(
            exec_id,
            ExecutionStatus.COMPLETED,
            logs_summary=f"Completed {len(ctx.task_configs)} tasks. Result: {result_text[:200]}..."
        )

        return True, exec_logger.get_all_logs(), None, evolution_context

    except Exception as e:
        error_msg = str(e)
        exec_logger.error(f"Execution failed: {error_msg}")
        exec_logger.error(traceback.format_exc())

        execution_service.update_execution_status(
            exec_id,
            ExecutionStatus.FAILED,
            error_message=error_msg,
            logs_summary=f"Failed: {error_msg[:200]}"
        )

        return False, exec_logger.get_all_logs(), error_msg, None


async def run_crew_async(exec_id: str, requirement: str, input_folder: Optional[str], crew_id: str, output_dir: str):
    """
    异步执行 Crew (使用线程池避免阻塞事件循环)
    执行成功后自动触发偏好进化提案生成
    """
    loop = asyncio.get_event_loop()
    success, logs, error, evolution_context = await loop.run_in_executor(
        None,  # 使用默认线程池
        _sync_run_crew,
        exec_id, requirement, input_folder, crew_id, output_dir
    )
    
    # 执行成功后，异步触发偏好进化（不阻塞返回结果）
    if success and evolution_context:
        try:
            from crewai_web.web.services.preferences_evolution_service import get_preferences_evolution_service
            
            evolution_service = get_preferences_evolution_service()
            
            # 创建后台任务生成提案（不 await，让它在后台运行）
            asyncio.create_task(_generate_evolution_proposal(evolution_service, evolution_context))
            
            logger = logging.getLogger(__name__)
            logger.info(f"[Evolution] Scheduled preference evolution for execution {exec_id}")
            
        except Exception as e:
            # 偏好进化失败不应影响主流程
            logger = logging.getLogger(__name__)
            logger.error(f"[Evolution] Failed to schedule evolution: {e}")
    
    return success, logs, error


async def _generate_evolution_proposal(service, evolution_context: dict):
    """后台生成偏好进化提案"""
    try:
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"[Evolution] Generating proposal for execution {evolution_context['exec_id']}...")
        
        proposal = await service.generate_proposal(
            exec_id=evolution_context["exec_id"],
            exec_topic=evolution_context["exec_topic"],
            requirement=evolution_context["requirement"],
            crew_config=evolution_context["crew_config"],
            agents_config=evolution_context["agents_config"],
            tasks_config=evolution_context["tasks_config"],
            execution_result=evolution_context["execution_result"],
            user_interventions=evolution_context.get("user_interventions", [])
        )
        
        logger.info(f"[Evolution] Proposal generated: {len(proposal.suggestions)} suggestions")
        logger.info(f"[Evolution] View at: /api/preferences/proposals/{evolution_context['exec_id']}")
        
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"[Evolution] Failed to generate proposal: {e}")
