"""
EventChain - 责任链执行引擎

将多个 BaseEvent 组装成 chain，依次执行。
如果某个节点抛异常，chain 中断。

使用方式:
    chain = EventChain()
    chain.add(PreHandleEvent())
    chain.add(BusinessEvent())
    chain.add(FinishEvent())
    chain.add(TouchEvent())
    
    ctx = chain.execute(ExecutionContext(crew_id="xxx", ...))
"""

import logging
from typing import List

from crewai_web.core.chain.events.base_event import BaseEvent, ExecutionContext

logger = logging.getLogger(__name__)


class EventChain:
    """
    责任链执行引擎
    
    类似 Java:
        public class EventChain {
            private List<BaseEvent> events;
            public ExecutionContext execute(ExecutionContext ctx);
        }
    """
    
    def __init__(self):
        self.events: List[BaseEvent] = []
    
    def add(self, event: BaseEvent) -> "EventChain":
        """
        添加事件节点（支持链式调用）
        
        Args:
            event: 事件节点
            
        Returns:
            self（链式调用）
        """
        self.events.append(event)
        return self
    
    def execute(self, ctx: ExecutionContext) -> ExecutionContext:
        """
        执行整个责任链
        
        Args:
            ctx: 初始执行上下文
            
        Returns:
            最终执行上下文
        """
        chain_names = " → ".join(e.name for e in self.events)
        logger.info(f"[Chain] Starting: {chain_names}")
        ctx.log("INFO", f"[Chain] Pipeline: {chain_names}")
        
        for i, event in enumerate(self.events):
            step = f"[{i + 1}/{len(self.events)}]"
            
            try:
                logger.info(f"[Chain] {step} Executing {event.name} (type={event.event_type.value})")
                ctx = event.handle(ctx)
                logger.info(f"[Chain] {step} {event.name} ✅ completed")
                
            except Exception as e:
                logger.error(f"[Chain] {step} {event.name} ❌ failed: {e}")
                ctx.error = str(e)
                ctx.success = False
                ctx.log("ERROR", f"[Chain] {step} {event.name} failed: {e}")
                
                # 尝试执行剩余的收尾节点（FinishEvent/TouchEvent）
                self._run_cleanup(ctx, i + 1)
                raise
        
        logger.info("[Chain] ✅ All events completed successfully")
        return ctx
    
    def _run_cleanup(self, ctx: ExecutionContext, start_index: int) -> None:
        """
        失败后尝试执行收尾节点
        
        即使 BusinessEvent 失败了，也要尝试执行 FinishEvent 和 TouchEvent，
        保证日志保存和失败通知能发出去。
        """
        from crewai_web.core.chain.events.base_event import EventType
        
        for event in self.events[start_index:]:
            if event.event_type == EventType.STANDARD:
                try:
                    logger.info(f"[Chain] Cleanup: executing {event.name}")
                    event.handle(ctx)
                except Exception as cleanup_error:
                    logger.error(f"[Chain] Cleanup {event.name} also failed: {cleanup_error}")


def build_default_chain() -> EventChain:
    """
    构建默认的执行链

    PreHandleEvent → BusinessEventDispatcher → FinishEvent → TouchEvent
                            ↓
                    Strategy.schedule([
                        BusinessEvent(Task1, Agent1),
                        BusinessEvent(Task2, Agent2),
                        ...
                    ])
    """
    from crewai_web.core.chain.events import PreHandleEvent, BusinessEventDispatcher, FinishEvent, TouchEvent

    return (
        EventChain()
        .add(PreHandleEvent())
        .add(BusinessEventDispatcher())
        .add(FinishEvent())
        .add(TouchEvent())
    )
