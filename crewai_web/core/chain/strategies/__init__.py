"""调度策略"""

from crewai_web.core.chain.strategies.scheduling_strategy import (
    SchedulingStrategy,
    get_strategy,
    register_strategy,
    STRATEGY_REGISTRY,
)

# 导入子类触发 @register_strategy 注册
import crewai_web.core.chain.strategies.sequential_strategy  # noqa: F401
import crewai_web.core.chain.strategies.hierarchical_strategy  # noqa: F401

__all__ = [
    "SchedulingStrategy",
    "get_strategy",
    "register_strategy",
    "STRATEGY_REGISTRY",
]
