"""
AI 生成结果的 Pydantic 校验模型
确保 LLM 返回的 JSON 格式正确
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class TaskPlan(BaseModel):
    """任务规划"""
    name: str = Field(..., description="任务名称，简洁，10字内")
    description: str = Field(..., description="任务描述，详细说明要做什么")
    expected_output: str = Field(..., description="期望输出，明确的交付物")
    role_type: str = Field(..., description="所需角色类型，如：产品经理、技术专家")
    dependencies: List[str] = Field(default_factory=list, description="依赖的任务名称列表")


class TasksPlanResponse(BaseModel):
    """任务列表响应"""
    tasks: List[TaskPlan] = Field(..., description="任务列表，1-5个")


class AgentConfig(BaseModel):
    """Agent 配置"""
    role: str = Field(..., description="角色名称，简洁")
    goal: str = Field(..., description="目标，一句话")
    backstory: str = Field(..., description="背景故事，2-3句话")


class AgentMatchResult(BaseModel):
    """Agent 匹配结果"""
    matched: bool = Field(..., description="是否找到匹配的 Agent")
    agent_id: Optional[str] = Field(None, description="匹配的 Agent ID，如果 matched=false 则为 null")
    reason: str = Field(..., description="匹配理由或未匹配原因")


class AgentModelAssignment(BaseModel):
    """单个 Agent 的模型分配"""
    agent_id: str = Field(..., description="Agent ID")
    agent_role: str = Field(..., description="Agent 角色名称")
    assigned_model_tier: str = Field(..., description="分配的模型等级：basic/standard/advanced")
    reason: str = Field(..., description="分配理由")
    tasks: List[str] = Field(default_factory=list, description="该 Agent 负责的任务列表")
    task_complexity: str = Field(..., description="任务复杂度：low/medium/high")


class ModelAssignmentSummary(BaseModel):
    """模型分配汇总"""
    total_agents: int = Field(..., description="总 Agent 数量")
    basic_count: int = Field(..., description="使用 basic 模型的 Agent 数量")
    standard_count: int = Field(..., description="使用 standard 模型的 Agent 数量")
    advanced_count: int = Field(..., description="使用 advanced 模型的 Agent 数量")
    optimization_note: str = Field(..., description="优化说明")


class ModelAssignmentResponse(BaseModel):
    """模型分配响应"""
    assignments: List[AgentModelAssignment] = Field(..., description="每个 Agent 的模型分配")
    summary: ModelAssignmentSummary = Field(..., description="分配汇总")
