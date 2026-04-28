"""
执行日志领域模型
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ExecutionStatus(str, Enum):
    """执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class LogEntry(BaseModel):
    """单条日志"""
    timestamp: datetime
    level: str
    message: str
    logger_name: Optional[str] = None


class ExecutionLog(BaseModel):
    """执行日志记录"""
    id: str = Field(..., description="执行ID")
    scenario: str = Field(..., description="场景描述")
    status: ExecutionStatus = Field(default=ExecutionStatus.PENDING)
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    topic: Optional[str] = None
    crew_id: Optional[str] = None
    agent_ids: List[str] = Field(default_factory=list)
    task_ids: List[str] = Field(default_factory=list)
    
    logs: List[LogEntry] = Field(default_factory=list)
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ExecutionLogCreate(BaseModel):
    """创建执行日志"""
    scenario: str
    context: Optional[str] = None
    doc_filename: Optional[str] = None
