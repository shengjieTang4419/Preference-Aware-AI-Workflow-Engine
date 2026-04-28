"""
PreHandleEvent - 预处理事件

责任链第一个节点，负责：
1. 校验 crew_id 是否存在
2. 校验 agent_ids 是否都存在
3. 校验 task_ids 是否都存在
4. 校验 task 的 agent_id 是否都能匹配到 agent
5. 将加载好的配置写入 context，供后续节点使用
"""

from crewai_web.core.chain.events.base_event import BaseEvent, EventType, ExecutionContext


class PreHandleEvent(BaseEvent):
    """预处理事件 - 校验整个 chain 的合法性"""
    
    def __init__(self):
        super().__init__(EventType.STANDARD)
    
    def handle(self, ctx: ExecutionContext) -> ExecutionContext:
        self.logger.info(f"[PreHandle] Validating chain for crew={ctx.crew_id}")
        ctx.log("INFO", f"[PreHandle] Starting validation for crew: {ctx.crew_id}")
        
        # 1. 校验 crew 存在
        from crewai_web.web.services import crew_service, agent_service, task_service
        
        crew_config = crew_service.get_crew(ctx.crew_id)
        if not crew_config:
            raise ValueError(f"Crew '{ctx.crew_id}' not found")
        
        ctx.crew_config = crew_config
        ctx.log("INFO", f"[PreHandle] Crew loaded: {crew_config.name} (process_type={crew_config.process_type})")
        
        # 2. 校验并加载所有 agents
        for agent_id in crew_config.agent_ids:
            agent = agent_service.get_agent(agent_id)
            if not agent:
                raise ValueError(f"Agent '{agent_id}' not found (referenced by crew '{ctx.crew_id}')")
            ctx.agent_configs[agent_id] = agent
        
        ctx.log("INFO", f"[PreHandle] Agents validated: {len(ctx.agent_configs)} agents")
        
        # 3. 校验并加载所有 tasks
        for task_id in crew_config.task_ids:
            task = task_service.get_task(task_id)
            if not task:
                raise ValueError(f"Task '{task_id}' not found (referenced by crew '{ctx.crew_id}')")
            ctx.task_configs[task_id] = task
        
        ctx.log("INFO", f"[PreHandle] Tasks validated: {len(ctx.task_configs)} tasks")
        
        # 4. 校验 task 的 agent_id 能匹配到 agent
        for task_id, task_config in ctx.task_configs.items():
            if task_config.agent_id not in ctx.agent_configs:
                raise ValueError(
                    f"Task '{task_id}' references agent '{task_config.agent_id}' "
                    f"which is not in crew's agent list"
                )
        
        # 5. 校验 context_task_ids 引用合法
        task_id_set = set(ctx.task_configs.keys())
        for task_id, task_config in ctx.task_configs.items():
            if task_config.context_task_ids:
                for dep_id in task_config.context_task_ids:
                    if dep_id not in task_id_set:
                        self.logger.warning(
                            f"[PreHandle] Task '{task_id}' depends on '{dep_id}' which is not in task list"
                        )
        
        ctx.log("INFO", "[PreHandle] ✅ All validations passed")
        
        return ctx
