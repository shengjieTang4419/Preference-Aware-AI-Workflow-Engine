"""LLM 调用服务 — 薄封装层

为需要调用 LLM 的业务服务提供统一入口。
"""
import logging
from typing import Optional

from crewai_web.core.ai import AIClient

logger = logging.getLogger(__name__)


async def call_llm(prompt: str, system_prompt: Optional[str] = None) -> str:
    """调用默认 LLM，返回文本响应"""
    client = AIClient.get_default()
    return await client.call(prompt=prompt, system_prompt=system_prompt)
