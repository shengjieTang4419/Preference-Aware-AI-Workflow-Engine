from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class TaskBase(BaseModel):
    name: str = Field(..., description="Task标识名")
    description: str
    expected_output: str
    agent_id: str  # 关联的 agent
    context_task_ids: List[str] = []  # 前置依赖 tasks
    async_execution: bool = False
    
    # 新增：归属信息（让 Task 知道自己属于哪个 Crew/Topic）
    topic: Optional[str] = Field(None, description="所属项目主题")
    crew_id: Optional[str] = Field(None, description="所属 Crew ID")
    execution_id: Optional[str] = Field(None, description="创建该 Task 的执行 ID")
    
    # 新增：角色信息（记录原始的角色需求）
    role_type: Optional[str] = Field(None, description="任务所需角色类型（如：产品经理、技术专家）")


class TaskCreate(TaskBase):
    """创建 Task 时的数据模型"""
    pass


class TaskUpdate(BaseModel):
    description: Optional[str] = None
    expected_output: Optional[str] = None
    agent_id: Optional[str] = None
    context_task_ids: Optional[List[str]] = None
    async_execution: Optional[bool] = None


class TaskOut(TaskBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
