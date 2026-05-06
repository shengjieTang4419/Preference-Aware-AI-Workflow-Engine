"""Crew 构建辅助类

职责：
- 从 BusinessEvent 列表构建 Agents
- 从 BusinessEvent 列表构建 Tasks
- 处理模型分配逻辑

设计原则：组合优于继承
- 不是基类方法，而是独立的 Helper
- Strategy 通过组合使用，而不是继承
"""

import logging
from typing import Dict, List, Tuple, Any

from crewai_web.core.chain.events.base_event import ExecutionContext
from crewai_web.core.chain.crew_builder import CrewBuilder

logger = logging.getLogger(__name__)


class CrewBuilderHelper:
    """Crew 构建辅助类
    
    提供通用的 Agent 和 Task 构建逻辑，供 Strategy 组合使用。
    """
    
    def __init__(self, builder: CrewBuilder):
        """初始化
        
        Args:
            builder: CrewBuilder 实例
        """
        self.builder = builder
    
    def build_agents(
        self,
        events: List["BusinessEvent"],  # noqa: F821
        ctx: ExecutionContext,
    ) -> Dict[str, Any]:
        """构建所有 Agent（去重）
        
        Args:
            events: BusinessEvent 列表
            ctx: 执行上下文
            
        Returns:
            agent_id -> Agent 对象的映射
        """
        agent_model_assignments = getattr(ctx.crew_config, "agent_model_assignments", None) or {}
        logger.info(f"[CrewBuilderHelper] Agent model assignments: {agent_model_assignments}")

        agents_map = {}
        for event in events:
            agent_id = event.task_config.agent_id
            if agent_id not in agents_map:
                agent_config = ctx.agent_configs[agent_id]
                model_tier = agent_model_assignments.get(agent_id)
                agents_map[agent_id] = self.builder.build_agent(agent_config, ctx.inputs, model_tier)

        logger.info(f"[CrewBuilderHelper] Built {len(agents_map)} agents")
        return agents_map
    
    def build_tasks(
        self,
        events: List["BusinessEvent"],  # noqa: F821
        agents_map: Dict[str, Any],
        ctx: ExecutionContext,
    ) -> Tuple[List[Any], Dict[str, Any]]:
        """构建所有 Task
        
        Args:
            events: BusinessEvent 列表
            agents_map: agent_id -> Agent 对象的映射
            ctx: 执行上下文
            
        Returns:
            (tasks_list, tasks_map) 元组
        """
        tasks_list = []
        tasks_map = {}

        for event in events:
            task_config = event.task_config
            agent = agents_map[task_config.agent_id]

            # 构建 context_tasks
            context_tasks = []
            if task_config.context_task_ids:
                for dep_id in task_config.context_task_ids:
                    if dep_id in tasks_map:
                        context_tasks.append(tasks_map[dep_id])

            task = self.builder.build_task(task_config, agent, context_tasks, ctx.inputs)
            tasks_map[event.task_id] = task
            tasks_list.append(task)

        logger.info(f"[CrewBuilderHelper] Built {len(tasks_list)} tasks")
        return tasks_list, tasks_map
