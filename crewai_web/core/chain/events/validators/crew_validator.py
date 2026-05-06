"""Crew 配置校验器"""

from crewai_web.core.chain.events.base_event import ExecutionContext
from .resource_validator import ResourceValidator


class CrewValidator:
    """Crew 配置校验器
    
    专门用于校验 Crew 配置的完整性和一致性。
    
    职责：
    - 校验 Crew 存在
    - 校验 Agents 存在
    - 校验 Tasks 存在
    - 校验 Task → Agent 引用关系
    - 校验 Task → Task 依赖关系
    
    依赖：
    - ResourceValidator: 通用资源校验器
    """
    
    def __init__(self, ctx: ExecutionContext, validator: ResourceValidator):
        """初始化 Crew 校验器
        
        Args:
            ctx: 执行上下文
            validator: 通用资源校验器
        """
        self.ctx = ctx
        self.validator = validator
    
    def validate_crew(self, crew_service) -> None:
        """校验 Crew 存在
        
        Args:
            crew_service: Crew 服务
            
        Raises:
            ValueError: 如果 Crew 不存在
        """
        crew_config = self.validator.validate_resource(
            resource_id=self.ctx.crew_id,
            resource_type="Crew",
            fetch_func=crew_service.get_crew,
        )
        self.ctx.crew_config = crew_config
        self.ctx.log("INFO", f"[Validator] Crew loaded: {crew_config.name} (process_type={crew_config.process_type})")
    
    def validate_agents(self, agent_service) -> None:
        """校验所有 Agents 存在
        
        Args:
            agent_service: Agent 服务
            
        Raises:
            ValueError: 如果任何 Agent 不存在
        """
        self.validator.validate_resources(
            resource_ids=self.ctx.crew_config.agent_ids,
            resource_type="Agent",
            fetch_func=agent_service.get_agent,
            storage=self.ctx.agent_configs,
            error_context=f"referenced by crew '{self.ctx.crew_id}'",
        )
    
    def validate_tasks(self, task_service) -> None:
        """校验所有 Tasks 存在
        
        Args:
            task_service: Task 服务
            
        Raises:
            ValueError: 如果任何 Task 不存在
        """
        self.validator.validate_resources(
            resource_ids=self.ctx.crew_config.task_ids,
            resource_type="Task",
            fetch_func=task_service.get_task,
            storage=self.ctx.task_configs,
            error_context=f"referenced by crew '{self.ctx.crew_id}'",
        )
    
    def validate_task_agent_references(self) -> None:
        """校验 Task 的 agent_id 引用合法
        
        确保每个 Task 引用的 Agent 都在 Crew 的 Agent 列表中。
        
        Raises:
            ValueError: 如果 Task 引用了不存在的 Agent
        """
        for task_id, task_config in self.ctx.task_configs.items():
            self.validator.validate_reference(
                source_id=task_id,
                target_id=task_config.agent_id,
                valid_ids=set(self.ctx.agent_configs.keys()),
                error_message=f"Task '{task_id}' references agent '{task_config.agent_id}' which is not in crew's agent list",
            )
    
    def validate_task_context_references(self) -> None:
        """校验 Task 的 context_task_ids 引用合法
        
        确保每个 Task 的依赖 Task 都在 Crew 的 Task 列表中。
        注意：这里只是警告，不抛出异常。
        """
        task_id_set = set(self.ctx.task_configs.keys())
        for task_id, task_config in self.ctx.task_configs.items():
            if task_config.context_task_ids:
                for dep_id in task_config.context_task_ids:
                    if dep_id not in task_id_set:
                        # 这里只是警告，不抛异常
                        self.ctx.log(
                            "WARNING",
                            f"[Validator] Task '{task_id}' depends on '{dep_id}' which is not in task list",
                        )
