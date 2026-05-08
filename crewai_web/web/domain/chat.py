"""
Chat 相关领域模型
"""
from pydantic import BaseModel
from typing import Optional


class ChatStreamRequest(BaseModel):
    """流式对话请求"""
    scenario: str
    doc_filename: Optional[str] = None
