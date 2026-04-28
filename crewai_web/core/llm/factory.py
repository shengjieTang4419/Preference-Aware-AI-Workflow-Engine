import os
from typing import Optional
from crewai import LLM
from .base_provider import BaseLLMProvider
from .dashscope_provider import DashScopeProvider
from .claude_provider import ClaudeProvider


class LLMFactory:
    
    def __init__(self):
        self.providers: dict[str, BaseLLMProvider] = {
            "dashscope": DashScopeProvider(),
            "claude": ClaudeProvider(),
        }
        self.default_provider = os.getenv("DEFAULT_LLM_PROVIDER", "dashscope")
    
    def get_llm(self, agent_name: Optional[str] = None, provider: Optional[str] = None, model: Optional[str] = None, **kwargs) -> LLM:
        if agent_name:
            agent_config = os.getenv(f"AGENT_{agent_name.upper()}_LLM")
            if agent_config:
                provider, model = self._parse_config(agent_config)
        
        provider = provider or self.default_provider
        
        if provider not in self.providers:
            raise ValueError(f"Unsupported LLM provider: {provider}. Available: {list(self.providers.keys())}")
        
        llm_provider = self.providers[provider]
        
        if not llm_provider.validate_config():
            raise ValueError(f"Provider '{provider}' is not properly configured")
        
        model = model or llm_provider.get_default_model()
        
        return llm_provider.create_llm(model, **kwargs)
    
    def _parse_config(self, config: str) -> tuple[str, str]:
        if ":" in config:
            provider, model = config.split(":", 1)
            return provider.strip(), model.strip()
        return self.default_provider, config.strip()
    
    def get_provider(self, provider_name: str) -> BaseLLMProvider:
        if provider_name not in self.providers:
            raise ValueError(f"Unknown provider: {provider_name}")
        return self.providers[provider_name]
    
    def list_providers(self) -> list[dict]:
        result = []
        for name, provider in self.providers.items():
            result.append({
                "name": name,
                "display_name": name.title(),
                "is_configured": provider.validate_config(),
                "available_models": provider.get_available_models(),
                "default_model": provider.get_default_model(),
            })
        return result


llm_factory = LLMFactory()


def get_llm_for_agent(agent_name: str, **kwargs) -> LLM:
    return llm_factory.get_llm(agent_name=agent_name, **kwargs)


def get_default_llm(**kwargs) -> LLM:
    return llm_factory.get_llm(**kwargs)
