"""
创建 Tasks 事件
"""
from crewai_web.core.event import BusinessEvent, EventContext
from crewai_web.web.services.task_generator import task_generator


class CreateTasksEvent(BusinessEvent):
    """步骤 5: 创建 Tasks"""

    name = "创建任务"
    step = 5
    total = 7

    async def do_execute(self, ctx: EventContext) -> None:
        ctx.task_ids = task_generator.create_tasks(
            ctx.tasks_plan,
            ctx.agents_mapping,
            topic=ctx.topic,
            crew_id=ctx.crew_id,
            execution_id=ctx.execution_id,
        )
