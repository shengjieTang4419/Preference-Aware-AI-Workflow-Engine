"""
AI 模型分配事件
"""
from crewai_web.core.event import BusinessEvent, EventContext
from crewai_web.web.services.model_assignment_service import model_assignment_service


class AssignModelsEvent(BusinessEvent):
    """步骤 6: AI 模型分配"""

    name = "分配 AI 模型"
    step = 6
    total = 9

    async def do_execute(self, ctx: EventContext) -> None:
        ctx.agent_model_assignments = await model_assignment_service.assign_models_for_crew(
            crew_name=ctx.topic,
            process_type="sequential",
            agent_ids=list(ctx.agents_mapping.values()),
            task_ids=ctx.task_ids,
        )
