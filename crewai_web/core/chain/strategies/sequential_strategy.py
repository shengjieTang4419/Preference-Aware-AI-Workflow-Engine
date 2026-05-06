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
from crewai_web.core.chain.strategies.crew_builder_helper import CrewBuilderHelper

logger = logging.getLogger(__name__)


@register_strategy("sequential")
class SequentialStrategy(SchedulingStrategy):
    """顺序执行：Task1 → Task2 → Task3 → ...

    设计原则：组合优于继承
    - 通过 CrewBuilderHelper 组合通用逻辑
    - 而不是从基类继承方法
    """

    def schedule(
        self,
        events: List["BusinessEvent"],  # noqa: F821
        ctx: ExecutionContext,
    ) -> ExecutionContext:
        logger.info(f"[Sequential] Scheduling {len(events)} business events")

        # 组合 Helper（而不是继承）
        builder = CrewBuilder()
        helper = CrewBuilderHelper(builder)

        # 构建 Agents 和 Tasks
        agents_map = helper.build_agents(events, ctx)
        tasks_list, _ = helper.build_tasks(events, agents_map, ctx)

        # 创建并执行 Crew
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
