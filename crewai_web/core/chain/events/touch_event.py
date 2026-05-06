"""
TouchEvent - 消息触达事件

责任链最后一个节点，负责：
- 发送执行完成通知（钉钉、企业微信、Slack 等）

注意：
- 偏好进化已在 FinishEvent 中触发，这里不再处理
- 只负责通知，保持职责单一
"""

from crewai_web.core.chain.events.base_event import BaseEvent, EventType, ExecutionContext
from crewai_web.core.chain.events.templates import generate_success_notification, generate_failure_notification
from crewai_web.core.alerters import create_alerter_from_env


class TouchEvent(BaseEvent):
    """消息触达事件 - 发送通知

    职责：
    - 发送执行完成/失败通知

    设计原则：
    - 单一职责：只负责通知，不处理其他业务逻辑
    - 使用模板：通知消息由 Template 生成
    """

    def __init__(self):
        super().__init__(EventType.STANDARD)

    def handle(self, ctx: ExecutionContext) -> ExecutionContext:
        """发送通知"""
        ctx.log("INFO", "[Touch] Starting notification delivery")

        self._send_notification(ctx)

        ctx.log("INFO", "[Touch] ✅ Notification delivery completed")

        return ctx

    def _send_notification(self, ctx: ExecutionContext) -> None:
        """发送执行完成通知"""
        alerter = create_alerter_from_env()
        if not alerter:
            ctx.log("INFO", "[Touch] No alerter configured, skip notification")
            return

        # 生成通知消息（使用模板）
        crew_name = ctx.crew_config.name if ctx.crew_config else ctx.crew_id

        if ctx.success:
            message = generate_success_notification(
                crew_name=crew_name,
                exec_id=ctx.exec_id,
                duration=ctx.duration_seconds,
                result=ctx.result,
            )
        else:
            message = generate_failure_notification(
                crew_name=crew_name,
                exec_id=ctx.exec_id,
                error=ctx.error,
            )

        # 发送通知
        try:
            alerter.send(message)
            ctx.log("INFO", "[Touch] Notification sent successfully")
        except Exception as e:
            ctx.log("WARNING", f"[Touch] Failed to send notification: {e}")
