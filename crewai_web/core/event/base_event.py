"""
BaseEvent - 抽象基类，定义事件契约
"""
from abc import ABC, abstractmethod
from .event_context import EventContext


class BaseEvent(ABC):
    """事件基类 - 定义执行契约"""

    @property
    @abstractmethod
    def name(self) -> str:
        """事件名称（用于日志和通知）"""
        ...

    @property
    @abstractmethod
    def step(self) -> int:
        """当前步骤序号"""
        ...

    @property
    @abstractmethod
    def total(self) -> int:
        """总步骤数"""
        ...

    @abstractmethod
    async def do_execute(self, ctx: EventContext) -> None:
        """子类实现的具体业务逻辑"""
        ...
