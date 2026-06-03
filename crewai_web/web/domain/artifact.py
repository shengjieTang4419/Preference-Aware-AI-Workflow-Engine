"""制品执行领域模型

定义制品Skill执行相关的数据结构。
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import json


class SkillExecStatus(str, Enum):
    """单个Skill执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ArtifactSkillExecCreate(BaseModel):
    """创建Skill执行记录"""
    execution_id: str
    skill_name: str
    step_index: int = 0


class ArtifactSkillExecUpdate(BaseModel):
    """更新Skill执行记录"""
    status: Optional[str] = None
    input_summary: Optional[str] = None
    output_files: Optional[List[str]] = None
    output_metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ArtifactSkillExecOut(BaseModel):
    """Skill执行记录输出"""
    id: int
    execution_id: str
    skill_name: str
    step_index: int
    status: str
    input_summary: Optional[str] = None
    output_files: List[str] = []
    output_metadata: Dict[str, Any] = {}
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    @field_validator("output_files", mode="before")
    @classmethod
    def parse_output_files(cls, v: Any) -> list:
        if v is None:
            return []
        return v

    @field_validator("output_metadata", mode="before")
    @classmethod
    def parse_output_metadata(cls, v: Any) -> dict:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return {}
        if v is None:
            return {}
        return v

    class Config:
        from_attributes = True


class SkillResult(BaseModel):
    """单个Skill执行结果"""
    skill_name: str
    success: bool
    output_text: str = ""           # 文本输出（给下一个skill的输入）
    output_files: List[str] = []    # 产出文件路径列表
    output_metadata: Dict[str, Any] = {}
    error_message: Optional[str] = None


class ArtifactResult(BaseModel):
    """制品最终结果"""
    skill_chain: List[str]          # 执行的skill链
    success: bool
    title: str = ""
    description: str = ""
    output_type: str = ""           # pptx/docx/xlsx/mp4/...
    output_files: List[str] = []    # 最终产出文件
    preview_text: str = ""
    error_message: Optional[str] = None
