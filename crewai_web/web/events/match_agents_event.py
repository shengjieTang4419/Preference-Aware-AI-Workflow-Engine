"""
匹配/创建 Agents 事件
"""
from crewai_web.core.event import BusinessEvent, EventContext
from crewai_web.web.services.agent_generator import agent_generator


class MatchAgentsEvent(BusinessEvent):
    """步骤 3: 匹配或创建 Agents"""

    name = "匹配/创建 Agent"
    step = 3
    total = 9

    async def do_execute(self, ctx: EventContext) -> None:
        ctx.agents_mapping = await agent_generator.match_or_create_agents(ctx.tasks_plan)
