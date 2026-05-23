from fastapi import APIRouter, HTTPException, Depends
from typing import List

from crewai_web.web.api.deps import get_required_user_id
from crewai_web.web.domain.membership import (
    MembershipOut, ActivateCodeRequest, PurchaseRequest,
    TransactionOut, PricingPlan,
)
from crewai_web.web.services import membership_service

router = APIRouter(prefix="/membership", tags=["membership"])


@router.get("/me", response_model=MembershipOut)
async def get_my_membership(user_id: int = Depends(get_required_user_id)):
    """获取当前会员信息"""
    return await membership_service.get_membership(user_id)


@router.get("/plans", response_model=List[PricingPlan])
async def get_plans():
    """获取定价方案"""
    return membership_service.PRICING_PLANS


@router.post("/activate", response_model=MembershipOut)
async def activate_code(req: ActivateCodeRequest, user_id: int = Depends(get_required_user_id)):
    """激活码升级"""
    try:
        return await membership_service.activate_code(user_id, req.code)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/purchase", response_model=MembershipOut)
async def purchase(req: PurchaseRequest, user_id: int = Depends(get_required_user_id)):
    """充值会员"""
    try:
        return await membership_service.purchase_membership(user_id, req.level, req.months)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/transactions", response_model=List[TransactionOut])
async def list_transactions(user_id: int = Depends(get_required_user_id)):
    """获取充值流水"""
    return await membership_service.list_transactions(user_id)


@router.get("/installed-scenes", response_model=List[str])
async def get_installed_scenes(user_id: int = Depends(get_required_user_id)):
    """获取已安装的场景 ID 列表"""
    return await membership_service.get_user_installed_scenes(user_id)


@router.post("/install-scene/{scene_id}")
async def install_scene(scene_id: str, user_id: int = Depends(get_required_user_id)):
    """安装场景"""
    try:
        await membership_service.install_scene(user_id, scene_id)
        return {"status": "ok", "message": f"场景 {scene_id} 已安装"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
