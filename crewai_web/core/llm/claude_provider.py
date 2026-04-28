import os
from typing import Optional
from crewai import LLM
from .base_provider import BaseLLMProvider


class ClaudeProvider(BaseLLMProvider):
    
    BASE_URL = "https://api.anthropic.com/v1"
    
    def __init__(self):
        self.api_key = os.getenv("CLAUDE_API_KEY")
        self.base_url = os.getenv("CLAUDE_BASE_URL", self.BASE_URL)
        self.default_temperature = float(os.getenv("CLAUDE_TEMPERATURE", "0.7"))
    
    def create_llm(self, model: str, **kwargs) -> LLM:
        if not self.validate_config():
            raise ValueError("Claude API Key not configured. Please set CLAUDE_API_KEY in .env")
        
        temperature = kwargs.get("temperature", self.default_temperature)
        
        return LLM(
            model=f"anthropic/{model}",
            api_key=self.api_key,
            base_url=self.base_url,
            temperature=temperature,
        )
    
    def validate_config(self) -> bool:
        return bool(self.api_key)
    
    def get_provider_name(self) -> str:
        return "claude"
    
    def get_available_models(self) -> list[str]:
        models_env = os.getenv("CLAUDE_AVAILABLE_MODELS", "")
        if models_env:
            return [m.strip() for m in models_env.split(",")]
        return []
    
    def get_default_model(self) -> str:
        """获取默认模型（从 JSON 配置或 .env 读取）"""
        from crewai_web.web.domain import LLMConfig
        
        try:
            # 从配置系统加载（支持 JSON 热更新）
            config = LLMConfig.load()
            if config.claude:
                # 返回默认模型
                default_model = config.claude.default_model
                return default_model.model
        except Exception:
            pass
        
        # 回退到环境变量（向后兼容）
        return os.getenv("CLAUDE_MODEL_SONNET", "claude-sonnet-4.6")
