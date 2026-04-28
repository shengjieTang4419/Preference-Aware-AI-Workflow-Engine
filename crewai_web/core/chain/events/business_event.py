"""
BusinessEvent - 业务执行事件

一个 BusinessEvent = 一个 Agent 执行一个 Task。

N 个 BusinessEvent 由 SchedulingStrategy 编排执行顺序。
BusinessEvent 自身不知道自己在链中的位置，调度由 Strategy 负责。

BusinessEventDispatcher 是固定链中的节点，负责：
1. 从 ctx 中读取 crew_config，生成 N 个 BusinessEvent
2. 根据 process_type 选择 SchedulingStrategy
3. 把 N 个 BusinessEvent 交给 Strategy 执行
"""

from datetime import datetime
from typing import Any

from crewai_web.core.chain.events.base_event import BaseEvent, EventType, ExecutionContext


class BusinessEvent:
    """
    单个业务执行事件 = 一个 Agent 执行一个 Task

    这不是 BaseEvent 的子类，因为它不是链中的固定节点，
    而是被 Strategy 动态编排的执行单元。

    类似 Java:
        public class BusinessEvent {
            String taskId;
            AgentConfig agentConfig;
            TaskConfig taskConfig;
        }
    """

    def __init__(self, task_id: str, agent_config: Any, task_config: Any):
        self.task_id = task_id
        self.agent_config = agent_config
        self.task_config = task_config

    def __repr__(self) -> str:
        return f"BusinessEvent(task={self.task_id}, agent={self.task_config.agent_id})"


class BusinessEventDispatcher(BaseEvent):
    """
    业务事件调度器 - 固定链中的节点

    职责：
    1. 从 ctx 生成 N 个 BusinessEvent
    2. 选择 SchedulingStrategy
    3. 把 BusinessEvent 列表交给 Strategy 执行

    在 chain 中的位置是固定的：
        PreHandle → [BusinessEventDispatcher] → Finish → Touch
                          ↓
                    Strategy.schedule([
                        BusinessEvent(Task1, Agent1),
                        BusinessEvent(Task2, Agent2),
                        BusinessEvent(Task3, Agent3),
                    ])
    """

    def __init__(self):
        super().__init__(EventType.STANDARD)

    def handle(self, ctx: ExecutionContext) -> ExecutionContext:
        process_type = ctx.crew_config.process_type
        ctx.log("INFO", f"[Dispatcher] Generating business events for crew={ctx.crew_id}")

        # 1. 生成 N 个 BusinessEvent
        business_events = self._create_business_events(ctx)
        ctx.log("INFO", f"[Dispatcher] Created {len(business_events)} business events")
        for event in business_events:
            ctx.log("INFO", f"[Dispatcher]   - {event}")

        # 2. 选择调度策略
        from crewai_web.core.chain.strategies.scheduling_strategy import get_strategy

        strategy = get_strategy(process_type)
        ctx.log("INFO", f"[Dispatcher] Strategy: {strategy.name} (process_type={process_type})")

        # 3. 记录开始时间
        ctx.metrics["start_time"] = datetime.now()

        try:
            # 4. 交给 Strategy 执行
            ctx = strategy.schedule(business_events, ctx)

            ctx.metrics["end_time"] = datetime.now()
            ctx.log("INFO", f"[Dispatcher] ✅ All business events completed")

        except Exception as e:
            ctx.metrics["end_time"] = datetime.now()
            ctx.error = str(e)
            ctx.success = False
            ctx.log("ERROR", f"[Dispatcher] ❌ Execution failed: {e}")
            raise

        return ctx

    def _create_business_events(self, ctx: ExecutionContext) -> list[BusinessEvent]:
        """从 ctx 中的配置生成 BusinessEvent 列表"""
        events = []

        for task_id in ctx.crew_config.task_ids:
            task_config = ctx.task_configs[task_id]
            agent_config = ctx.agent_configs[task_config.agent_id]

            events.append(BusinessEvent(
                task_id=task_id,
                agent_config=agent_config,
                task_config=task_config,
            ))

        return events
