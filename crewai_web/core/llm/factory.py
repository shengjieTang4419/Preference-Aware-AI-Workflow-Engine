from typing import Optional
from crewai import LLM
from .provider_registry import provider_registry
from .config_loader import config_loader


class LLMFactory:
    """LLM 工厂
    
    职责：调度和组装，将请求委托给正确的 Provider
    核心逻辑在 BaseLLMProvider.create_llm() 和相关工具类中
    """
    
    def __init__(self):
        self.registry = provider_registry
    
    def get_llm(
        self, 
        provider: Optional[str] = None, 
        model: Optional[str] = None, 
        **kwargs
    ) -> LLM:
        """创建 LLM 实例（调度入口）
        
        Args:
            provider: Provider 名称（可选，默认从配置读取）
            model: 模型名称（可选，默认使用 Provider 的默认模型）
            **kwargs: 额外参数（如 temperature）
            
        Returns:
            LLM: 创建好的 LLM 实例
            
        Examples:
            # 使用默认配置（default_provider + is_default=true 的模型）
            llm = factory.get_llm()
            
            # 指定 Provider，使用默认模型
            llm = factory.get_llm(provider="claude")
            
            # 指定 Provider 和模型
            llm = factory.get_llm(provider="dashscope", model="qwen3.6-max-preview")
            
            # 覆盖 temperature
            llm = factory.get_llm(temperature=0.9)
        """
        # 1. 确定 Provider（从参数或配置）
        provider_name = provider or config_loader.get_default_provider()
        
        # 2. 获取 Provider 实例
        llm_provider = self.registry.get_provider(provider_name)
        
        # 3. 验证配置
        if not llm_provider.validate_config():
            raise ValueError(
                f"Provider '{provider_name}' is not properly configured. "
                f"Check API key in .env file."
            )
        
        # 4. 委托给 Provider（Provider 负责决策和创建）
        return (
            llm_provider.create_llm(model, **kwargs) if model
            else llm_provider.get_default_llm(**kwargs)
        )

llm_factory = LLMFactory()


def get_default_llm(**kwargs) -> LLM:
    """获取默认 LLM（便捷函数）
    
    等价于 llm_factory.get_llm(**kwargs)
    """
    return llm_factory.get_llm(**kwargs)
