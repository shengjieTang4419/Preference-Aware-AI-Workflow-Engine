"""
PreHandleEvent - 预处理事件

责任链第一个节点，负责校验并加载 Crew 配置。
"""

from crewai_web.core.chain.events.base_event import BaseEvent, EventType, ExecutionContext
from crewai_web.core.chain.events.validators import ResourceValidator, CrewValidator
from crewai_web.web.services import crew_service, agent_service, task_service


class PreHandleEvent(BaseEvent):
    """预处理事件 - 校验并加载配置"""

    def __init__(self):
        super().__init__(EventType.STANDARD)

    def handle(self, ctx: ExecutionContext) -> ExecutionContext:
        """校验 Crew 配置的完整性和一致性"""
        self.logger.info(f"[PreHandle] Validating chain for crew={ctx.crew_id}")
        ctx.log("INFO", f"[PreHandle] Starting validation for crew: {ctx.crew_id}")

        # 创建校验器
        resource_validator = ResourceValidator(ctx)
        crew_validator = CrewValidator(ctx, resource_validator)

        # 执行校验流程
        crew_validator.validate_crew(crew_service)
        crew_validator.validate_agents(agent_service)
        crew_validator.validate_tasks(task_service)
        crew_validator.validate_task_agent_references()
        crew_validator.validate_task_context_references()

        ctx.log("INFO", "[PreHandle] ✅ All validations passed")

        return ctx
