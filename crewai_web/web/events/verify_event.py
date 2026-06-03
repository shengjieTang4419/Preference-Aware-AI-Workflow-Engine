"""
Finish 复验事件 - 更新 Crew 配置，验证完整性
"""
from crewai_web.core.event import BusinessEvent, EventContext
from crewai_web.web.services import crew_service
from crewai_web.web.domain.crew import CrewUpdate


class VerifyEvent(BusinessEvent):
    """步骤 7: Finish 复验 - 更新 Crew 并验证"""

    name = "复验并更新 Crew"
    step = 7
    total = 9

    async def do_execute(self, ctx: EventContext) -> None:
        # 更新 Crew（task_ids + agent_model_assignments）
        crew_service.update_crew(
            ctx.crew_id,
            CrewUpdate(
                task_ids=ctx.task_ids,
                agent_model_assignments=ctx.agent_model_assignments,
            ),
        )
        ctx.success = True
