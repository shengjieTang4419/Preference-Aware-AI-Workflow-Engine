"""创作域 — Pydantic 模型

定义创作执行请求 / 响应的数据结构。
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime


class CreativityExecuteRequest(BaseModel):
    """创作执行请求"""
    scene_id: str = Field(..., description="场景 ID，如 document / data-analysis")
    input_text: str = Field(..., description="用户输入的想法或需求")
    input_files: List[str] = Field(default_factory=list, description="上传的文件路径列表")


class CreativityExecuteResponse(BaseModel):
    """创作执行响应"""
    execution_id: str = Field(..., description="执行 ID")
    status: str = Field(default="pending", description="执行状态: pending/running/completed/failed")
    artifact: Optional["ArtifactOut"] = None


class ArtifactOut(BaseModel):
    """制品输出"""
    id: int
    execution_id: str
    user_id: Optional[int] = None
    scene_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    output_type: Optional[str] = None
    output_dir: Optional[str] = None
    output_files: List[str] = Field(default_factory=list)
    preview_text: Optional[str] = None
    status: str = "pending"
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    @field_validator("output_files", mode="before")
    @classmethod
    def _ensure_list(cls, v):
        """数据库 NULL 转为空列表"""
        return v if v is not None else []

    class Config:
        from_attributes = True
