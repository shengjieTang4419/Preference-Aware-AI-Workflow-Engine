"""
SchedulingStrategy - 调度策略基类

定义 BusinessEvent 的编排接口。
策略只负责：拿到 N 个 BusinessEvent，决定怎么执行它们。
"""

from abc import ABC, abstractmethod
from typing import Dict, List

from crewai_web.core.chain.events.base_event import ExecutionContext


class SchedulingStrategy(ABC):
    """
    调度策略基类

    类似 Java:
        public interface SchedulingStrategy {
            void schedule(List<BusinessEvent> events, ExecutionContext ctx);
        }

    职责：
        - 接收 N 个 BusinessEvent
        - 根据策略决定执行顺序
        - 执行并将结果写入 ctx
    """

    @abstractmethod
    def schedule(
        self,
        events: List["BusinessEvent"],  # noqa: F821 - forward ref
        ctx: ExecutionContext,
    ) -> ExecutionContext:
        """
        编排并执行 BusinessEvent 列表

        Args:
            events: BusinessEvent 列表
            ctx: 执行上下文

        Returns:
            更新后的执行上下文
        """
        pass

    @property
    def name(self) -> str:
        return self.__class__.__name__


# ============================================================
# 策略注册表
# 新增策略只需：1. 写一个子类  2. 在这里注册
# ============================================================

STRATEGY_REGISTRY: Dict[str, type[SchedulingStrategy]] = {}


def register_strategy(process_type: str):
    """装饰器：注册调度策略"""

    def decorator(cls: type[SchedulingStrategy]):
        STRATEGY_REGISTRY[process_type] = cls
        return cls

    return decorator


def get_strategy(process_type: str) -> SchedulingStrategy:
    """
    根据 process_type 获取调度策略实例

    Args:
        process_type: 调度类型（来自 crew 配置的 process_type 字段）

    Returns:
        对应的策略实例

    Raises:
        ValueError: 不支持的调度类型
    """
    strategy_cls = STRATEGY_REGISTRY.get(process_type)
    if not strategy_cls:
        supported = ", ".join(STRATEGY_REGISTRY.keys())
        raise ValueError(
            f"Unsupported process_type '{process_type}'. Supported: {supported}"
        )
    return strategy_cls()
