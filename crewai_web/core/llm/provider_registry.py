"""LLM Provider 注册表"""
from typing import Dict
from .base_provider import BaseLLMProvider
from .dashscope_provider import DashScopeProvider
from .claude_provider import ClaudeProvider
from .config_loader import config_loader


class ProviderRegistry:
    """LLM Provider 注册表
    
    职责：
    1. 管理所有 Provider 实例
    2. 提供 Provider 查询接口
    """
    
    def __init__(self):
        # 注册所有 Provider
        self._providers: Dict[str, BaseLLMProvider] = {
            "dashscope": DashScopeProvider(),
            "claude": ClaudeProvider(),
        }
    
    @property
    def default_provider(self) -> str:
        """获取默认 Provider（从配置读取）"""
        return config_loader.get_default_provider()
    
    def get_provider(self, provider_name: str) -> BaseLLMProvider:
        """获取指定的 Provider
        
        Args:
            provider_name: Provider 名称（如 "dashscope", "claude"）
            
        Returns:
            BaseLLMProvider: Provider 实例
            
        Raises:
            ValueError: 如果 Provider 不存在
        """
        if provider_name not in self._providers:
            raise ValueError(
                f"Unknown provider: {provider_name}. "
                f"Available: {list(self._providers.keys())}"
            )
        return self._providers[provider_name]
    
    def list_providers(self) -> list[dict]:
        """获取所有 Provider 的配置状态
        
        Returns:
            list[dict]: Provider 列表，每个包含：
                - name: Provider 名称
                - display_name: 显示名称
                - is_configured: 是否已配置（API Key 存在）
                - default_model: 默认模型名称
        """
        result = []
        
        for name, provider in self._providers.items():
            default_model_name = None
            
            try:
                default_tier = config_loader.get_default_tier(provider.platform)
                default_model_name = default_tier.model
            except Exception:
                pass  # 如果读取失败，default_model 为 None
            
            result.append({
                "name": name,
                "display_name": name.title(),
                "is_configured": provider.validate_config(),
                "default_model": default_model_name,
            })
        
        return result
    
    def register_provider(self, name: str, provider: BaseLLMProvider) -> None:
        """注册新的 Provider（用于扩展）
        
        Args:
            name: Provider 名称
            provider: Provider 实例
        """
        self._providers[name] = provider


# 全局单例
provider_registry = ProviderRegistry()
