"""
配置管理服务
职责：LLM 配置读取、.env 文件更新、敏感信息脱敏
"""
import os
import logging
from pathlib import Path
from typing import Optional

from crewai_web.web.config import ENV_FILE

logger = logging.getLogger(__name__)


class ConfigService:

    def get_llm_settings(self) -> dict:
        """获取当前 LLM 配置（热加载，优先级：JSON > .env）"""
        from crewai_web.web.domain import LLMConfig
        
        # 每次都重新加载配置（支持热更新）
        config = LLMConfig.load()
        
        # 转换为 API 响应格式
        return config.to_api_response()

    def update_llm_settings(self, settings) -> None:
        """更新 LLM 配置到 JSON 文件（立即生效，无需重启）"""
        from crewai_web.web.domain import LLMConfig
        from crewai_web.web.config import STORAGE_DIR
        
        json_path = STORAGE_DIR / "config" / "llm_settings.json"
        
        # 转换为领域模型
        config = LLMConfig(**settings.model_dump())
        
        # 保存到 JSON（不包含 API Key）
        config.save(json_path)
        
        logger.info(f"Updated LLM settings to {json_path} (hot reload enabled)")

    def _collect_provider_updates(self, updates: dict, prefix: str, config) -> None:
        """收集某个 provider 的配置更新"""
        if config.api_key:
            updates[f"{prefix}_API_KEY"] = config.api_key
        if config.base_url:
            updates[f"{prefix}_BASE_URL"] = config.base_url
        
        # 三级模型配置
        if config.basic:
            updates[f"{prefix}_MODEL_BASIC"] = config.basic.model
            updates[f"{prefix}_MODEL_BASIC_TEMP"] = str(config.basic.temperature)
        
        if config.standard:
            updates[f"{prefix}_MODEL_STANDARD"] = config.standard.model
            updates[f"{prefix}_MODEL_STANDARD_TEMP"] = str(config.standard.temperature)
        
        if config.advanced:
            updates[f"{prefix}_MODEL_ADVANCED"] = config.advanced.model
            updates[f"{prefix}_MODEL_ADVANCED_TEMP"] = str(config.advanced.temperature)
        
        # 保存默认模型等级
        default_tier = "standard"  # 默认值
        if config.basic and getattr(config.basic, 'is_default', False):
            default_tier = "basic"
        elif config.standard and getattr(config.standard, 'is_default', False):
            default_tier = "standard"
        elif config.advanced and getattr(config.advanced, 'is_default', False):
            default_tier = "advanced"
        updates[f"{prefix}_DEFAULT_TIER"] = default_tier

    def _update_env_file(self, updates: dict[str, str]) -> None:
        """更新 .env 文件"""
        env_file = ENV_FILE
        if not env_file.exists():
            env_file.touch()

        lines = env_file.read_text().splitlines() if env_file.exists() else []

        existing_keys = set()
        new_lines = []

        for line in lines:
            if "=" in line and not line.strip().startswith("#"):
                key = line.split("=", 1)[0].strip()
                if key in updates:
                    new_lines.append(f"{key}={updates[key]}")
                    existing_keys.add(key)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)

        for key, value in updates.items():
            if key not in existing_keys:
                new_lines.append(f"{key}={value}")

        env_file.write_text("\n".join(new_lines) + "\n")


_config_service: Optional[ConfigService] = None


def get_config_service() -> ConfigService:
    global _config_service
    if _config_service is None:
        _config_service = ConfigService()
    return _config_service
