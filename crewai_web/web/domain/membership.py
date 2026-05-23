from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class MembershipOut(BaseModel):
    """会员信息输出"""
    user_id: int
    level: str = "free"
    activation_code: Optional[str] = None
    activated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_expired: bool = False
    virtual_money: float = 0

    class Config:
        from_attributes = True


class ActivateCodeRequest(BaseModel):
    """激活码请求"""
    code: str = Field(..., description="激活码")


class PurchaseRequest(BaseModel):
    """充值请求"""
    level: str = Field(..., description="目标等级: pro/max")
    months: int = Field(1, ge=1, le=36, description="月数")


class TransactionOut(BaseModel):
    """充值流水输出"""
    id: int
    user_id: int
    action: str
    from_level: Optional[str] = None
    to_level: Optional[str] = None
    amount: float = 0
    activation_code: Optional[str] = None
    remark: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PricingPlan(BaseModel):
    """定价方案"""
    level: str
    name: str
    price: float
    period: str
    features: list[str]
    scene_access: str
