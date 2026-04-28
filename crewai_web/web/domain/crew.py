from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class CrewBase(BaseModel):
    name: str
    description: Optional[str] = None
    agent_ids: List[str] = []  # 引用的 agents
    task_ids: List[str] = []   # 引用的 tasks（顺序即执行顺序）
    process_type: str = "sequential"  # sequential | hierarchical
    
    # 新增：Agent 模型等级分配 (agent_id -> model_tier)
    # model_tier: "basic" | "standard" | "advanced"
    agent_model_assignments: Optional[Dict[str, str]] = Field(
        default_factory=dict,
        description="Agent ID 到模型等级的映射，如 {'agent_1': 'advanced', 'agent_2': 'standard'}"
    )


class CrewCreate(CrewBase):
    pass


class CrewUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    agent_ids: Optional[List[str]] = None
    task_ids: Optional[List[str]] = None
    process_type: Optional[str] = None
    agent_model_assignments: Optional[Dict[str, str]] = None


class CrewOut(CrewBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
