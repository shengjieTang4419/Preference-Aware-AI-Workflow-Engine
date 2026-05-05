"""
HierarchicalStrategy - 层级执行策略

CrewAI 的 hierarchical 模式：由一个 manager agent 自动分配任务给子 agent。
"""

import logging
from typing import List

from crewai import Crew, Process

from crewai_web.core.chain.events.base_event import ExecutionContext
from crewai_web.core.chain.strategies.scheduling_strategy import SchedulingStrategy, register_strategy
from crewai_web.core.chain.crew_builder import CrewBuilder

logger = logging.getLogger(__name__)


@register_strategy("hierarchical")
class HierarchicalStrategy(SchedulingStrategy):
    """层级执行：Manager Agent 自动编排子 Agent"""

    def schedule(
        self,
        events: List["BusinessEvent"],  # noqa: F821
        ctx: ExecutionContext,
    ) -> ExecutionContext:
        logger.info(f"[Hierarchical] Scheduling {len(events)} business events")

        builder = CrewBuilder()

        # 获取 agent_model_assignments
        agent_model_assignments = getattr(ctx.crew_config, "agent_model_assignments", None) or {}
        logger.info(f"[Hierarchical] Agent model assignments: {agent_model_assignments}")

        # 构建所有 Agent
        agents_map = {}
        for event in events:
            agent_id = event.task_config.agent_id
            if agent_id not in agents_map:
                agent_config = ctx.agent_configs[agent_id]

                # 解析该 Agent 的模型档位
                model_tier = agent_model_assignments.get(agent_id)

                agents_map[agent_id] = builder.build_agent(agent_config, ctx.inputs, model_tier)

        # 构建所有 Task
        tasks_list = []
        tasks_map = {}

        for event in events:
            task_config = event.task_config
            agent = agents_map[task_config.agent_id]

            context_tasks = []
            if task_config.context_task_ids:
                for dep_id in task_config.context_task_ids:
                    if dep_id in tasks_map:
                        context_tasks.append(tasks_map[dep_id])

            task = builder.build_task(task_config, agent, context_tasks, ctx.inputs)
            tasks_map[event.task_id] = task
            tasks_list.append(task)

        # 用 CrewAI hierarchical 模式执行
        from pathlib import Path

        crew = Crew(
            agents=list(agents_map.values()),
            tasks=tasks_list,
            process=Process.hierarchical,
            verbose=True,
            memory=False,
            checkpoint=True,
            output_log_file=str(Path(ctx.output_dir) / "execution.log") if ctx.output_dir else None,
        )

        ctx.crew_instance = crew
        result = crew.kickoff(inputs=ctx.inputs)
        ctx.result = str(result)
        ctx.success = True

        return ctx
