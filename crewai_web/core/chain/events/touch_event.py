"""
TouchEvent - 消息触达事件

责任链最后一个节点，负责：
1. 发送执行完成通知（钉钉、企业微信、Slack 等）
2. 触发偏好进化（如果执行成功）
"""

from crewai_web.core.chain.events.base_event import BaseEvent, EventType, ExecutionContext
from crewai_web.core.alerters import create_alerter_from_env


class TouchEvent(BaseEvent):
    """消息触达事件 - 通知和后续触发"""
    
    def __init__(self):
        super().__init__(EventType.STANDARD)
    
    def handle(self, ctx: ExecutionContext) -> ExecutionContext:
        ctx.log("INFO", "[Touch] Starting message delivery")
        
        # 1. 发送通知
        self._send_notification(ctx)
        
        # 2. 触发偏好进化
        if ctx.success:
            self._trigger_evolution(ctx)
        
        ctx.log("INFO", "[Touch] ✅ Message delivery completed")
        
        return ctx
    
    def _send_notification(self, ctx: ExecutionContext) -> None:
        """发送执行完成通知"""
        alerter = create_alerter_from_env()
        if not alerter:
            ctx.log("INFO", "[Touch] No alerter configured, skip notification")
            return
        
        crew_name = ctx.crew_config.name if ctx.crew_config else ctx.crew_id
        duration = ctx.duration_seconds
        
        if ctx.success:
            message = (
                f"✅ Crew 执行完成\n"
                f"Crew: {crew_name}\n"
                f"Execution: {ctx.exec_id}\n"
                f"Duration: {f'{duration:.2f}s' if duration else 'N/A'}\n"
                f"Result: {ctx.result[:200] if ctx.result else 'N/A'}..."
            )
        else:
            message = (
                f"❌ Crew 执行失败\n"
                f"Crew: {crew_name}\n"
                f"Execution: {ctx.exec_id}\n"
                f"Error: {ctx.error or 'Unknown error'}"
            )
        
        try:
            alerter.send(message)
            ctx.log("INFO", "[Touch] Notification sent")
        except Exception as e:
            ctx.log("WARNING", f"[Touch] Failed to send notification: {e}")
    
    def _trigger_evolution(self, ctx: ExecutionContext) -> None:
        """
        触发偏好进化提案
        
        数据已在 FinishEvent 准备好，这里只负责触发异步任务。
        """
        evolution_context = ctx.extras.get("evolution_context")
        if not evolution_context:
            ctx.log("INFO", "[Touch] No evolution context, skip evolution")
            return
        
        try:
            # TODO: 这里应该异步调用 preferences_evolution_service
            # 目前只是标记，实际触发由外部（如 crew_runner）处理
            ctx.log("INFO", f"[Touch] Evolution ready for exec_id={ctx.exec_id}")
            
        except Exception as e:
            ctx.log("WARNING", f"[Touch] Failed to trigger evolution: {e}")
