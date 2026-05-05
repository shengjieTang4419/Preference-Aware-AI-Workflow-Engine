import os
from typing import Optional
from crewai import LLM
from .base_provider import BaseLLMProvider
from .provider_utils import resolve_temperature


class ClaudeProvider(BaseLLMProvider):
    """Claude 提供商"""
    
    @property
    def platform(self) -> str:
        return "claude"
    
    def __init__(self):
        self.api_key = os.getenv("CLAUDE_API_KEY")
        self.base_url = os.getenv("CLAUDE_BASE_URL", "https://api.anthropic.com/v1")
    
    def create_llm(self, model: str, **kwargs) -> LLM:
        """创建 Claude LLM 实例
        
        Args:
            model: 模型名称（如 "claude-3-5-sonnet-20241022"）
            **kwargs: 额外参数
                - temperature: 温度参数（可选）
        
        优先级：kwargs 传入的 temperature > 配置文件中的 temperature > 默认值 0.7
        """
        if not self.validate_config():
            raise ValueError("Claude API Key not configured. Please set CLAUDE_API_KEY in .env")
        
        # 解析 temperature 参数（三级优先级）
        temperature = resolve_temperature(self.platform, model, kwargs, default_value=0.7)
        
        return LLM(
            model=f"anthropic/{model}",  # Claude 使用 Anthropic 格式
            api_key=self.api_key,
            base_url=self.base_url,
            temperature=temperature,
        )
