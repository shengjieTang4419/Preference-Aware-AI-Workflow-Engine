from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class SceneOut(BaseModel):
    """场景卡片输出"""
    id: str
    icon: str
    title: str
    subtitle: str
    placeholder: Optional[str] = None
    category: str = "document"
    tags: List[str] = Field(default_factory=list)
    output_format: str = "markdown"
    enabled: bool = True
    sort_order: int = 0

    class Config:
        from_attributes = True
