"""
偏好进化数据模型
"""
from typing import List
from pydantic import BaseModel, Field


class SuggestedPreference(BaseModel):
    """建议的偏好条目"""
    category: str = Field(..., description="所属章节，如 '编码规范'、'Agent 角色定义'")
    content: str = Field(..., description="建议添加的内容")
    reason: str = Field(..., description="推荐理由（基于本次执行的洞察）")
    confidence: float = Field(default=0.8, ge=0, le=1, description="置信度 0-1")
    source_exec_id: str = Field(..., description="来源执行 ID")


class PreferenceEvolutionProposal(BaseModel):
    """偏好进化提案 - 类似 Git PR"""
    exec_id: str
    exec_topic: str
    original_content: str  # 原始 preferences.md 完整内容
    suggested_content: str   # LLM 生成的建议完整内容
    diff_summary: str      # 变更摘要（人类可读）
    suggestions: List[SuggestedPreference]  # 结构化建议列表
    created_at: str
