"""
SequentialStrategy - 顺序执行策略

按顺序依次执行每个 BusinessEvent。
上一个 Task 的输出作为下一个 Task 的上下文。
"""

import logging
from typing import List

from crewai import Crew, Process

from crewai_web.core.chain.events.base_event import ExecutionContext
from crewai_web.core.chain.strategies.scheduling_strategy import SchedulingStrategy, register_strategy
from crewai_web.core.chain.crew_builder import CrewBuilder

logger = logging.getLogger(__name__)


@register_strategy("sequential")
class SequentialStrategy(SchedulingStrategy):
    """顺序执行：Task1 → Task2 → Task3 → ..."""

    def schedule(
        self,
        events: List["BusinessEvent"],  # noqa: F821
        ctx: ExecutionContext,
    ) -> ExecutionContext:
        logger.info(f"[Sequential] Scheduling {len(events)} business events")

        builder = CrewBuilder()

        # 获取 agent_model_assignments
        agent_model_assignments = getattr(ctx.crew_config, "agent_model_assignments", None) or {}
        logger.info(f"[Sequential] Agent model assignments: {agent_model_assignments}")

        # 构建所有 Agent
        agents_map = {}
        for event in events:
            agent_id = event.task_config.agent_id
            if agent_id not in agents_map:
                agent_config = ctx.agent_configs[agent_id]

                # 解析该 Agent 的模型档位
                model_tier = agent_model_assignments.get(agent_id)

                agents_map[agent_id] = builder.build_agent(agent_config, ctx.inputs, model_tier)

        # 按顺序构建 Task（前一个 Task 作为后一个的 context）
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

            task = builder.build_task(task_config, agent, context_tasks, ctx.inputs)
            tasks_map[event.task_id] = task
            tasks_list.append(task)

        # 用 CrewAI 执行
        from pathlib import Path

        crew = Crew(
            agents=list(agents_map.values()),
            tasks=tasks_list,
            process=Process.sequential,
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
