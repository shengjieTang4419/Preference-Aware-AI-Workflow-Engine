"""
生成 Topic 事件
"""

from crewai_web.core.event import BusinessEvent, EventContext
from crewai_web.core.ai.client import AIClient


class GenerateTopicEvent(BusinessEvent):
    """步骤 1: 生成项目主题"""

    name = "生成项目主题"
    step = 1
    total = 7

    async def do_execute(self, ctx: EventContext) -> None:
        ai_client = AIClient.get_default()

        prompt = ai_client.load_prompt("generator/topic.prompt", scenario=ctx.scenario)

        topic = await ai_client.call(prompt, role=self.role)
        ctx.topic = topic.strip()
