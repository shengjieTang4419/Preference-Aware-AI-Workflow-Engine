"""LLM 配置加载工具"""

from typing import Optional
from crewai_web.web.domain import LLMConfig, ProviderConfig, ModelTierConfig


class LLMConfigLoader:
    """LLM 配置加载器（单例模式）"""

    _instance: Optional["LLMConfigLoader"] = None
    _config: Optional[LLMConfig] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load(self, force_reload: bool = False) -> LLMConfig:
        """加载配置（带缓存）

        Args:
            force_reload: 是否强制重新加载
        """
        if self._config is None or force_reload:
            self._config = LLMConfig.load()
        return self._config

    def get_provider_config(self, platform: str) -> ProviderConfig:
        """获取指定平台的配置

        Args:
            platform: 平台名称（如 "dashscope", "claude"）

        Returns:
            ProviderConfig: 平台配置对象

        Raises:
            ValueError: 如果平台未配置
        """
        config = self.load()
        provider_config = getattr(config, platform, None)

        if not provider_config:
            raise ValueError(f"Provider '{platform}' not configured in llm_settings.json")

        return provider_config

    def get_default_tier(self, platform: str) -> ModelTierConfig:
        """获取指定平台的默认档位配置

        Args:
            platform: 平台名称

        Returns:
            ModelTierConfig: 默认档位配置（包含 model 和 temperature）
        """
        provider_config = self.get_provider_config(platform)
        return provider_config.default_model

    def get_tier_by_model(self, platform: str, model: str) -> Optional[ModelTierConfig]:
        """根据模型名称查找对应的档位配置

        Args:
            platform: 平台名称
            model: 模型名称

        Returns:
            ModelTierConfig: 档位配置，如果找不到返回 None
        """
        provider_config = self.get_provider_config(platform)
        return provider_config.get_tier_by_model(model)

    def get_default_provider(self) -> str:
        """获取默认 Provider 名称

        Returns:
            str: 默认 Provider 名称（如 "dashscope"）
        """
        config = self.load()
        return config.default_provider

    def get_model_config(self, provider: str, tier: str) -> Optional[dict]:
        """获取指定 provider 和档位的模型配置

        Args:
            provider: Provider 名称（如 "dashscope", "claude"）
            tier: 模型档位（"basic" | "standard" | "advanced"）

        Returns:
            dict: 包含 model 和 temperature 的配置字典，如果找不到返回 None
        """
        try:
            provider_config = self.get_provider_config(provider)
            tier_config = getattr(provider_config, tier, None)

            if tier_config:
                return {
                    "model": tier_config.model,
                    "temperature": tier_config.temperature,
                }
            return None
        except (ValueError, AttributeError):
            return None

    def get_model_config_by_default_provider(self, tier: str) -> dict:
        """获取默认 provider 下指定档位的模型配置

        Args:
            tier: 模型档位（"basic" | "standard" | "advanced"）

        Returns:
            dict: 包含 model 和 temperature 的配置字典

        Raises:
            ValueError: 如果找不到配置
        """
        provider = self.get_default_provider()
        config = self.get_model_config(provider, tier)

        if not config:
            raise ValueError(f"Model tier '{tier}' not found in default provider '{provider}'")

        return config


# 全局单例
config_loader = LLMConfigLoader()
