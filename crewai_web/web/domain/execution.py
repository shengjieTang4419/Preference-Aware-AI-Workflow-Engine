from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionCreate(BaseModel):
    requirement: str = Field(..., description="用户需求输入")
    input_folder: Optional[str] = None  # 服务器上的文件夹路径
    crew_id: str  # 使用的 Crew 配置
    output_dir: str  # 输出目录 (用户选择或自动生成)
    inputs: Optional[Dict[str, Any]] = None  # 占位符替换字典


class ExecutionOut(BaseModel):
    id: str
    status: ExecutionStatus
    requirement: str
    input_folder: Optional[str]
    crew_id: str
    output_dir: str
    inputs: Optional[Dict[str, Any]] = None
    logs_summary: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class ExecutionLogEntry(BaseModel):
    timestamp: datetime
    level: str  # INFO, ERROR, etc.
    message: str


class ExecutionLogs(BaseModel):
    execution_id: str
    logs: List[ExecutionLogEntry]


class ExecutionFile(BaseModel):
    name: str
    path: str  # 相对于 output_dir 的路径
    size: int
    is_dir: bool


class ExecutionFileTree(BaseModel):
    execution_id: str
    output_dir: str
    files: List[ExecutionFile]
