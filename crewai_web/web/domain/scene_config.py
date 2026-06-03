from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Any
from datetime import datetime
import json


class SceneConfigBase(BaseModel):
    """场景配置基础模型"""
    id: str = Field(..., description="场景标识")
    icon: str = Field(..., description="图标 emoji")
    title: str = Field(..., description="显示标题")
    subtitle: str = Field(..., description="副标题描述")
    placeholder: Optional[str] = Field(None, description="输入框提示")
    category: str = Field("document", description="分类: document/data/code/media")
    tags: List[str] = Field(default_factory=list, description="标签")
    output_format: str = Field("markdown", description="输出格式")
    enabled: bool = Field(True, description="是否启用")
    visible: bool = Field(True, description="是否在首页显示")
    sort_order: int = Field(0, description="排序权重")
    price_tier: str = Field("free", description="收费层级: free/basic/premium")
    exec_mode: str = Field("auto", description="执行模式: auto/manual")
    output_dir: Optional[str] = Field(None, description="自动模式下的输出目录")
    crew_template: Optional[str] = Field(None, description="Crew 模板")
    artifact_skills: List[str] = Field(default_factory=list, description="制品生成所需的Skill列表")
    description: Optional[str] = Field(None, description="详细说明")

    @field_validator("artifact_skills", mode="before")
    @classmethod
    def parse_artifact_skills(cls, v: Any) -> list:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return []
        if v is None:
            return []
        return v

    @field_validator("tags", mode="before")
    @classmethod
    def parse_tags(cls, v: Any) -> list:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return []
        if v is None:
            return []
        return v


class SceneConfigCreate(SceneConfigBase):
    """创建场景配置"""
    pass


class SceneConfigUpdate(BaseModel):
    """更新场景配置（全可选）"""
    icon: Optional[str] = None
    title: Optional[str] = None
    subtitle: Optional[str] = None
    placeholder: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    output_format: Optional[str] = None
    enabled: Optional[bool] = None
    visible: Optional[bool] = None
    sort_order: Optional[int] = None
    price_tier: Optional[str] = None
    exec_mode: Optional[str] = None
    output_dir: Optional[str] = None
    crew_template: Optional[str] = None
    artifact_skills: Optional[List[str]] = None
    description: Optional[str] = None


class SceneConfigOut(SceneConfigBase):
    """场景配置输出"""
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
