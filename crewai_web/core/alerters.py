"""告警发送器实现"""

import os
import logging
from typing import Protocol

logger = logging.getLogger(__name__)


class Alerter(Protocol):
    """告警发送器协议"""
    
    def send(self, message: str) -> None:
        """发送告警消息"""
        ...


class DingTalkAlerter:
    """钉钉告警"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send(self, message: str) -> None:
        try:
            import requests
            
            requests.post(
                self.webhook_url,
                json={
                    "msgtype": "text",
                    "text": {"content": f"CrewAI Alert:\n{message}"}
                },
                timeout=10
            )
            logger.info("Alert sent to DingTalk")
        except Exception as e:
            logger.error(f"Failed to send DingTalk alert: {e}")


class WeChatWorkAlerter:
    """企业微信告警"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send(self, message: str) -> None:
        try:
            import requests
            
            requests.post(
                self.webhook_url,
                json={
                    "msgtype": "text",
                    "text": {"content": message}
                },
                timeout=10
            )
            logger.info("Alert sent to WeChat Work")
        except Exception as e:
            logger.error(f"Failed to send WeChat Work alert: {e}")


class SlackAlerter:
    """Slack 告警"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send(self, message: str) -> None:
        try:
            import requests
            
            requests.post(
                self.webhook_url,
                json={"text": message},
                timeout=10
            )
            logger.info("Alert sent to Slack")
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")


class CompositeAlerter:
    """组合告警器 - 同时发送到多个渠道"""
    
    def __init__(self, *alerters: Alerter):
        self.alerters = list(alerters)
    
    def add_alerter(self, alerter: Alerter) -> None:
        self.alerters.append(alerter)
    
    def send(self, message: str) -> None:
        for alerter in self.alerters:
            try:
                alerter.send(message)
            except Exception as e:
                logger.error(f"Alerter {alerter.__class__.__name__} failed: {e}")


def create_alerter_from_env() -> Alerter | None:
    """从环境变量创建告警器"""
    alerters = []
    
    dingtalk_webhook = os.getenv("DINGTALK_WEBHOOK")
    if dingtalk_webhook:
        alerters.append(DingTalkAlerter(dingtalk_webhook))
    
    wechat_webhook = os.getenv("WECHAT_WEBHOOK")
    if wechat_webhook:
        alerters.append(WeChatWorkAlerter(wechat_webhook))
    
    slack_webhook = os.getenv("SLACK_WEBHOOK")
    if slack_webhook:
        alerters.append(SlackAlerter(slack_webhook))
    
    if not alerters:
        return None
    
    if len(alerters) == 1:
        return alerters[0]
    
    return CompositeAlerter(*alerters)
