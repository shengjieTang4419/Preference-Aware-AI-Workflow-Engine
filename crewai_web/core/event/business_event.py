"""
BusinessEvent - 模板方法，装饰 log + websocket
"""

import logging
from .base_event import BaseEvent
from .event_context import EventContext
from crewai_web.core.tools.execution_logger import execution_logger
from crewai_web.core.tools.websocket_manager import ws_manager

logger = logging.getLogger(__name__)


class BusinessEvent(BaseEvent):
    """
    业务事件基类 - Template Method 模式

    装饰器行为：
    - before: 日志 + WebSocket 通知（进行中）
    - after: 日志 + WebSocket 通知（完成）
    - on_error: 日志 + WebSocket 通知（失败）
    """

    @property
    def role(self) -> str:
        """调试角色名称，默认使用类名"""
        return self.__class__.__name__

    async def execute(self, ctx: EventContext) -> None:
        """模板方法 - 不要覆写此方法"""
        try:
            # before: 通知开始
            await self._before(ctx)

            # 执行业务逻辑
            await self.do_execute(ctx)

            # after: 通知完成
            await self._after(ctx)

        except Exception as e:
            # on_error: 通知失败
            await self._on_error(ctx, e)
            raise

    async def _before(self, ctx: EventContext) -> None:
        """前置装饰：日志 + WebSocket"""
        msg = f"⏳ {self.name}..."
        execution_logger.log(ctx.execution_id, "INFO", f"[{self.step}/{self.total}] {self.name} 开始")
        await ws_manager.send_progress(ctx.execution_id, msg, self.step, self.total, "running")

    async def _after(self, ctx: EventContext) -> None:
        """后置装饰：日志 + WebSocket"""
        msg = f"✅ {self.name} 完成"
        execution_logger.log(ctx.execution_id, "INFO", f"[{self.step}/{self.total}] {self.name} 完成")
        await ws_manager.send_progress(ctx.execution_id, msg, self.step, self.total, "success")

    async def _on_error(self, ctx: EventContext, error: Exception) -> None:
        """异常装饰：日志 + WebSocket"""
        msg = f"❌ {self.name} 失败：{str(error)}"
        execution_logger.log(ctx.execution_id, "ERROR", f"[{self.step}/{self.total}] {msg}")
        await ws_manager.send_progress(ctx.execution_id, msg, self.step, self.total, "error")
