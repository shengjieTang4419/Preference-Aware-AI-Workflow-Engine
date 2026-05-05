"""
AI Client - LLM 交互客户端

职责：
1. LLM 调用（文本生成、结构化生成）
2. 集成 Preferences 系统
3. 集成调试服务
"""

import os
import logging
import time
import asyncio
from pathlib import Path
from typing import Optional, TypeVar, Type, Union
from pydantic import BaseModel, ValidationError

from crewai_web.core.llm import LLMFactory, get_default_llm
from crewai_web.web.services.preferences_loader import get_preferences
from crewai_web.core.debug_service import DebugService
from crewai_web.core.json_utils import extract_json

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class AIClient:
    """LLM 交互客户端（AI 交互的唯一入口）

    职责：
    1. 封装所有 AI 交互（call 方法）
    2. 统一管理 LLM 创建
    3. 集成 Preferences、Debug

    使用场景：
    - 场景1（固定调用）：AIClient.get_default() - 使用默认配置
    - 场景2（动态调用）：AIClient.create(provider, model) - 自定义配置
    """

    # Prompts 目录路径
    PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts"

    def __init__(self, llm, debug_enabled: Optional[bool] = None, debug_dir: Optional[str] = None):
        """私有构造函数（请使用 get_default() 或 create() 创建实例）"""
        self.llm = llm
        self.model_name = getattr(self.llm, "model", "unknown")

        # 从环境变量读取 debug 配置
        if debug_enabled is None:
            debug_enabled = os.getenv("LLM_DEBUG_ENABLED", "false").lower() == "true"
        if debug_dir is None:
            debug_dir = os.getenv("LLM_DEBUG_DIR")

        # 初始化调试服务
        self.debug_service = DebugService(enabled=debug_enabled, output_dir=debug_dir)

        if debug_enabled:
            logger.info(f"🐛 LLM Debug enabled, logs will be saved to: {debug_dir or '.local/llm_debug'}")
            logger.info(f"📊 Using model: {self.model_name}")

    @classmethod
    def get_default(cls, **kwargs) -> "AIClient":
        """获取默认 AI 客户端（场景1：固定调用）

        使用默认 Provider 和默认模型（is_default=true）

        Args:
            **kwargs: 额外参数（如 temperature, debug_enabled）

        Returns:
            AIClient: 配置好的客户端实例

        Example:
            client = AIClient.get_default()
            response = await client.call("Hello")
        """

        # 提取 debug 相关参数
        debug_enabled = kwargs.pop("debug_enabled", None)
        debug_dir = kwargs.pop("debug_dir", None)

        # 创建默认 LLM
        llm = get_default_llm(**kwargs)

        return cls(llm, debug_enabled=debug_enabled, debug_dir=debug_dir)

    @classmethod
    def create(cls, provider: Optional[str] = None, model: Optional[str] = None, **kwargs) -> "AIClient":
        """创建自定义 AI 客户端（场景2：动态调用）

        Args:
            provider: Provider 名称（可选，默认使用配置）
            model: 模型名称（可选，默认使用 Provider 的默认模型）
            **kwargs: 额外参数（如 temperature, debug_enabled）

        Returns:
            AIClient: 配置好的客户端实例

        Example:
            # 使用 Claude 的高级模型
            client = AIClient.create(
                provider="claude",
                model="claude-3-opus-20240229",
                temperature=0.9
            )
            response = await client.call("Complex task")
        """

        # 提取 debug 相关参数
        debug_enabled = kwargs.pop("debug_enabled", None)
        debug_dir = kwargs.pop("debug_dir", None)

        # 创建 LLM
        factory = LLMFactory()
        llm = factory.get_llm(provider=provider, model=model, **kwargs)

        return cls(llm, debug_enabled=debug_enabled, debug_dir=debug_dir)

    def load_prompt(self, prompt_path: str, **kwargs) -> str:
        """
        加载 prompt 模板文件并填充变量

        Args:
            prompt_path: prompt 文件的相对路径（相对于 prompts 目录）
            **kwargs: 要填充到模板中的变量

        Returns:
            填充后的 prompt 字符串

        Example:
            prompt = client.load_prompt(
                "generator/topic.prompt",
                scenario="开发一个博客系统",
                context_section="使用 FastAPI"
            )
        """
        full_path = self.PROMPTS_DIR / prompt_path

        if not full_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {full_path}")

        template = full_path.read_text(encoding="utf-8")

        # 填充变量
        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required variable in prompt template: {e}")

    async def call(
        self,
        prompt: str,
        response_model: Optional[Type[T]] = None,
        system_prompt: Optional[str] = None,
        role: Optional[str] = None,
        inject_preferences: bool = False,
        max_retries: int = 3,
    ) -> Union[T, str]:
        """
        调用 LLM 并返回响应（支持文本或结构化）

        Args:
            prompt: 用户提示词
            response_model: Pydantic 响应模型（可选）
                - None: 返回纯文本
                - Type[T]: 返回结构化 Pydantic 模型
            system_prompt: 系统提示词（可选）
            role: 角色名称（用于调试）
            inject_preferences: 是否注入偏好规则和系统规则（默认 False）
                - False: 系统内置 AI 交互（prompts 下的 prompt）
                - True: Crew 动态编排（需要偏好规则）
            max_retries: 最大重试次数

        Returns:
            str: 当 response_model=None 时返回文本
            T: 当 response_model 有值时返回 Pydantic 模型实例
        """
        # 只有在明确要求注入偏好时才加载
        if inject_preferences and system_prompt is None:
            preferences = get_preferences()
            system_prompt = preferences.load()

        # 组装完整 prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        else:
            full_prompt = prompt

        self.debug.log_prompt(full_prompt, role=role, model=self.model_name)

        for attempt in range(max_retries):
            try:
                start_time = time.time()

                response = await asyncio.to_thread(self.llm.call, full_prompt)

                elapsed = time.time() - start_time
                self.debug.log_response(response, elapsed=elapsed, role=role, model=self.model_name)

                # 如果没有指定 response_model，直接返回文本
                if response_model is None:
                    return response

                # 否则解析为结构化数据
                json_data = extract_json(response)
                result = response_model.model_validate(json_data)

                return result

            except ValidationError as e:
                logger.warning(f"Validation failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"LLM call failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(1)
