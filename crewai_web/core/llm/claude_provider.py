import os
from typing import Optional
from crewai import LLM
from .base_provider import BaseLLMProvider
from .provider_utils import resolve_temperature


class ClaudeProvider(BaseLLMProvider):
    """Claude 提供商

    支持两种模式：
    1. 原生 Claude API (api.anthropic.com) - 使用 anthropic/ 前缀
    2. xiaomimimo.com 平台 - 使用 openai/ 前缀 (OpenAI 兼容格式)

    通过 CLAUDE_MODEL_PREFIX 环境变量区分：
    - "anthropic/": 原生模式
    - "openai/": xiaomimimo 兼容模式
    """

    @property
    def platform(self) -> str:
        return "claude"

    def __init__(self):
        self.api_key = os.getenv("CLAUDE_API_KEY")
        self.base_url = os.getenv("CLAUDE_BASE_URL", "https://api.anthropic.com/v1")
        # 模型前缀：原生 Claude 用 "anthropic/"，xiaomimimo 用 "openai/"
        self.model_prefix = os.getenv("CLAUDE_MODEL_PREFIX", "")

    def create_llm(self, model: str, **kwargs) -> LLM:
        """创建 Claude LLM 实例

        Args:
            model: 模型名称
                - 原生模式: 如 "claude-3-5-sonnet-20241022"
                - xiaomimimo 模式: 如 "mimo-v2.5", "mimo-v2.5-pro"
            **kwargs: 额外参数
                - temperature: 温度参数（可选）

        优先级：kwargs 传入的 temperature > 配置文件中的 temperature > 默认值 0.7
        """
        if not self.validate_config():
            raise ValueError("Claude API Key not configured. Please set CLAUDE_API_KEY in .env")

        # 解析 temperature 参数（三级优先级）
        temperature = resolve_temperature(self.platform, model, kwargs, default_value=0.7)

        # 根据配置决定模型名称格式
        full_model = f"{self.model_prefix}{model}" if self.model_prefix else model

        return LLM(
            model=full_model,
            api_key=self.api_key,
            base_url=self.base_url,
            temperature=temperature,
        )
