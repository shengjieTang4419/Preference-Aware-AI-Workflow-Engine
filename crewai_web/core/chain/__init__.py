"""
责任链事件系统

架构：
    PreHandleEvent → BusinessEvent → FinishEvent → TouchEvent

使用：
    from crewai_web.core.chain import execute
    
    ctx = execute(crew_id="xxx", requirement="xxx", exec_id="xxx", output_dir="xxx")
"""

from crewai_web.core.chain.events import (
    BaseEvent, EventType, ExecutionContext,
    PreHandleEvent, BusinessEvent, BusinessEventDispatcher,
    FinishEvent, TouchEvent,
)
from crewai_web.core.chain.strategies import (
    SchedulingStrategy, get_strategy, register_strategy,
)
from crewai_web.core.chain.event_chain import EventChain, build_default_chain


def execute(
    crew_id: str,
    requirement: str,
    exec_id: str,
    output_dir: str,
    inputs: dict | None = None,
    input_folder: str | None = None,
) -> ExecutionContext:
    """
    执行一次完整的 Crew 运行

    这是整个责任链的对外统一入口。

    链路：
        PreHandleEvent → BusinessEventDispatcher → FinishEvent → TouchEvent
                                ↓
                        Strategy.schedule([
                            BusinessEvent(Task1, Agent1),
                            BusinessEvent(Task2, Agent2),
                            ...
                        ])

    Args:
        crew_id: Crew ID
        requirement: 需求描述
        exec_id: 执行 ID
        output_dir: 输出目录
        inputs: 占位符替换字典
        input_folder: 输入文件夹路径

    Returns:
        ExecutionContext（包含结果、指标、日志等）
    """
    ctx = ExecutionContext(
        crew_id=crew_id,
        requirement=requirement,
        exec_id=exec_id,
        output_dir=output_dir,
        inputs=inputs or {},
        input_folder=input_folder,
    )

    chain = build_default_chain()
    return chain.execute(ctx)


__all__ = [
    "execute",
    "BaseEvent",
    "EventType",
    "ExecutionContext",
    "EventChain",
    "build_default_chain",
    "PreHandleEvent",
    "BusinessEvent",
    "BusinessEventDispatcher",
    "FinishEvent",
    "TouchEvent",
    "SchedulingStrategy",
    "get_strategy",
    "register_strategy",
]
