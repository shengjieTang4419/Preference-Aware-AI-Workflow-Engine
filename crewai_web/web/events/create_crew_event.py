"""
创建 Crew 事件
"""
from crewai_web.core.event import BusinessEvent, EventContext
from crewai_web.web.services import crew_service
from crewai_web.web.domain.crew import CrewCreate


class CreateCrewEvent(BusinessEvent):
    """步骤 4: 创建 Crew"""

    name = "创建 Crew"
    step = 4
    total = 7

    async def do_execute(self, ctx: EventContext) -> None:
        crew_data = CrewCreate(
            name=ctx.topic,
            description=f"AI 自动生成的 Crew：{ctx.topic}",
            agent_ids=list(ctx.agents_mapping.values()),
            task_ids=[],
            process_type="sequential",
        )
        created_crew = crew_service.create_crew(crew_data)
        ctx.crew_id = created_crew.id
