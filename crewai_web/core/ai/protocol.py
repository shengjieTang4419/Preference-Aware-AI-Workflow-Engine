"""LLM 调用协议定义"""

from typing import Protocol, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class PromptToText(Protocol):
    """文本生成协议：prompt -> text"""

    def __call__(self, prompt: str) -> str:
        """
        Args:
            prompt: 用户提示词

        Returns:
            LLM 响应文本
        """
        ...


class PromptToModel(Protocol):
    """结构化生成协议：prompt -> Pydantic Model"""

    def __call__(self, prompt: str, cls: type[T]) -> T:
        """
        Args:
            prompt: 用户提示词
            cls: Pydantic 模型类

        Returns:
            校验后的 Pydantic 模型实例
        """
        ...


class ImageToModel(Protocol):
    """图像理解协议：image + prompt -> Pydantic Model"""

    def __call__(self, prompt: str, image: bytes, cls: type[T]) -> T:
        """
        Args:
            prompt: 用户提示词
            image: 图像字节数据
            cls: Pydantic 模型类

        Returns:
            校验后的 Pydantic 模型实例
        """
        ...
