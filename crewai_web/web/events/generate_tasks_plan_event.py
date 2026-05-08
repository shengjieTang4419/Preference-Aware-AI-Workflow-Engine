"""
生成 Tasks 规划事件
"""

from crewai_web.core.event import BusinessEvent, EventContext
from crewai_web.web.services.task_generator import task_generator


class GenerateTasksPlanEvent(BusinessEvent):
    """步骤 2: 生成任务规划"""

    name = "规划任务"
    step = 2
    total = 7

    async def do_execute(self, ctx: EventContext) -> None:
        ctx.tasks_plan = await task_generator.generate_tasks_plan(ctx.scenario, ctx.topic, None)
