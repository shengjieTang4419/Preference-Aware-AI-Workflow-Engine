from abc import ABC, abstractmethod
from typing import Optional
from crewai import LLM
from .config_loader import config_loader
from .provider_utils import ensure_temperature


class BaseLLMProvider(ABC):
    """LLM 提供商基类
    
    子类需要：
    1. 在 __init__ 中设置：
       - self.api_key: API 密钥
       - self.base_url: API 基础 URL
    2. 实现抽象属性：
       - platform: 平台名称（如 "dashscope", "claude"）
    3. 实现抽象方法：
       - create_llm: 创建 LLM 实例
    """
    
    api_key: str | None
    base_url: str | None
    
    @property
    @abstractmethod
    def platform(self) -> str:
        """平台名称（用于从配置中读取对应的 provider config）"""
        pass
    
    @abstractmethod
    def create_llm(self, model: str, **kwargs) -> LLM:
        """创建 LLM 实例
        
        Args:
            model: 模型名称
            **kwargs: 额外参数（如 temperature）
        """
        pass
    
    def validate_config(self) -> bool:
        """验证配置（检查 API Key 是否存在）"""
        return bool(self.api_key)
    
    def get_default_llm(self, **kwargs) -> LLM:
        """获取默认 LLM（从 JSON 配置读取 is_default=true 的档位）
        
        Args:
            **kwargs: 额外参数
                - temperature: 如果传入，会覆盖配置文件中的默认值
        
        Returns:
            LLM: 创建好的 LLM 实例
        """
        # 从配置文件获取默认档位（is_default=true 的那个）
        default_tier = config_loader.get_default_tier(self.platform)
        
        # 确保 kwargs 中有 temperature（如果没有则使用配置文件的值）
        ensure_temperature(kwargs, default_tier.temperature)
        
        # 调用 create_llm 创建实例
        return self.create_llm(
            model=default_tier.model,
            **kwargs
        )
