"""JSON 工具函数"""

import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def extract_json(response: str, fallback: Optional[Any] = None) -> Any:
    """
    从 LLM 响应中提取 JSON
    
    支持：
    - 纯 JSON
    - ```json ... ``` 代码块
    - ``` ... ``` 代码块
    
    Args:
        response: LLM 响应文本
        fallback: 解析失败时的降级返回值
        
    Returns:
        解析后的 JSON 对象（dict 或 list）
        
    Raises:
        ValueError: 无法解析 JSON 且未提供 fallback
    """
    json_str = response.strip()
    
    if "```json" in json_str:
        json_str = json_str.split("```json")[1].split("```")[0].strip()
    elif "```" in json_str:
        json_str = json_str.split("```")[1].split("```")[0].strip()
    
    try:
        parsed = json.loads(json_str)
        logger.debug(f"[JSON Extract] ✅ type={type(parsed).__name__}")
        return parsed
        
    except json.JSONDecodeError as e:
        logger.error(f"[JSON Extract] ❌ parse_failed line={e.lineno} col={e.colno}")
        logger.error(f"[JSON Extract] content_preview: {json_str[:500]}")
        
        if fallback is not None:
            logger.warning(f"[JSON Extract] using fallback: {fallback}")
            return fallback
        raise ValueError(f"Failed to parse JSON from LLM response: {e}")
