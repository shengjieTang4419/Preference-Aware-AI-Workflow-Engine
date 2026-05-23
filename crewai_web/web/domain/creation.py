from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CreationCreate(BaseModel):
    """创建创作请求"""
    scene_id: str = Field(..., description="场景 ID")
    input_text: str = Field(..., description="用户输入")
    input_files: List[str] = Field(default_factory=list, description="上传的文件路径")


class CreationOut(BaseModel):
    """创作记录输出"""
    id: int
    user_id: Optional[int] = None
    scene_id: str
    input_text: Optional[str] = None
    input_files: List[str] = Field(default_factory=list)
    status: str = "pending"
    output_dir: Optional[str] = None
    output_files: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None
    execution_id: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
