from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class SkillsConfig(BaseModel):
    """Agent Skills 配置"""
    mode: str = "auto"  # auto | manual | hybrid
    preferred: List[str] = Field(default_factory=list, description="优先使用的 Skills")
    auto_match: bool = True  # 是否自动匹配相关 Skills
    include_patterns: List[str] = Field(default_factory=list, description="包含的 Skills 模式，如 ['python-*']")
    exclude_patterns: List[str] = Field(default_factory=list, description="排除的 Skills 模式，如 ['java-*']")


class AgentBase(BaseModel):
    name: str = Field(..., description="Agent标识名(文件名部分)")
    role: str
    goal: str
    backstory: str
    allow_delegation: bool = False
    max_execution_time: int = 450
    llm_key: Optional[str] = None  # 如 ceo, product_manager
    skills_config: Optional[SkillsConfig] = None  # Skills 配置（可选）


class AgentCreate(AgentBase):
    pass


class AgentUpdate(BaseModel):
    role: Optional[str] = None
    goal: Optional[str] = None
    backstory: Optional[str] = None
    allow_delegation: Optional[bool] = None
    max_execution_time: Optional[int] = None
    llm_key: Optional[str] = None
    skills_config: Optional[SkillsConfig] = None


class AgentOut(AgentBase):
    id: str  # 与 name 保持一致
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
