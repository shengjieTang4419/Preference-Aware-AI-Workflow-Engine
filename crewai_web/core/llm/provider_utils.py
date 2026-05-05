"""LLM Provider 工具函数"""
from typing import Any, Dict, Optional
from .config_loader import config_loader


def resolve_temperature(
    platform: str,
    model: str,
    kwargs: Dict[str, Any],
    default_value: float = 0.7
) -> float:
    """解析 temperature 参数（三级优先级）
    
    优先级：
    1. kwargs 中显式传入的 temperature（最高优先级）
    2. 配置文件中对应模型的 temperature
    3. 默认值（最低优先级）
    
    Args:
        platform: 平台名称（如 "dashscope", "claude"）
        model: 模型名称
        kwargs: 调用参数字典
        default_value: 默认温度值
        
    Returns:
        float: 最终使用的 temperature 值
    """
    # 优先级1：kwargs 中显式传入
    if "temperature" in kwargs:
        return kwargs["temperature"]
    
    # 优先级2：从配置文件读取
    try:
        tier_config = config_loader.get_tier_by_model(platform, model)
        if tier_config:
            return tier_config.temperature
    except Exception:
        pass  # 读取失败，继续使用默认值
    
    # 优先级3：默认值
    return default_value


def ensure_temperature(kwargs: Dict[str, Any], temperature: float) -> None:
    """确保 kwargs 中有 temperature 参数（如果没有则设置）
    
    Args:
        kwargs: 参数字典（会被修改）
        temperature: 要设置的温度值
    """
    if "temperature" not in kwargs:
        kwargs["temperature"] = temperature
