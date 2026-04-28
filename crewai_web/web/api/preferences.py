"""
偏好进化 API
"""
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from crewai_web.web.services.preferences_evolution_service import get_preferences_evolution_service

router = APIRouter(prefix="/preferences", tags=["preferences"])


class MergeRequest(BaseModel):
    exec_id: str


class RejectRequest(BaseModel):
    exec_id: str
    reason: Optional[str] = None


@router.get("/proposals")
def list_proposals(limit: int = 20):
    """获取所有偏好进化提案列表"""
    return get_preferences_evolution_service().list_proposals_summary(limit)


@router.get("/proposals/{exec_id}")
def get_proposal(exec_id: str):
    """获取单个提案的完整详情"""
    detail = get_preferences_evolution_service().get_proposal_detail(exec_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Proposal for execution {exec_id} not found")
    return detail


@router.get("/proposals/{exec_id}/diff")
def get_proposal_diff(exec_id: str):
    """获取可视化 diff（行级对比）"""
    diff = get_preferences_evolution_service().get_proposal_diff(exec_id)
    if not diff:
        raise HTTPException(status_code=404, detail=f"Proposal for execution {exec_id} not found")
    return diff


@router.post("/proposals/merge")
def merge_proposal(request: MergeRequest):
    """合并提案到 preferences.md"""
    if not get_preferences_evolution_service().merge_proposal(request.exec_id):
        raise HTTPException(status_code=400, detail="Failed to merge proposal")
    return {"status": "merged", "exec_id": request.exec_id, "message": "已成功合并到 preferences.md"}


@router.post("/proposals/reject")
def reject_proposal(request: RejectRequest):
    """拒绝提案"""
    if not get_preferences_evolution_service().reject_proposal(request.exec_id, request.reason):
        raise HTTPException(status_code=404, detail="Proposal not found")
    return {"status": "rejected", "exec_id": request.exec_id, "reason": request.reason}


@router.get("/current")
def get_current_preferences():
    """获取当前 preferences.md 的内容"""
    from crewai_web.web.services.preferences_loader import get_preferences
    loader = get_preferences()
    return {
        "content": loader.load_preferences_only(),
        "file_path": str(loader.preferences_file)
    }


@router.post("/evolve-from-execution/{exec_id}")
async def evolve_from_execution(exec_id: str):
    """基于某次执行生成偏好进化提案"""
    result = await get_preferences_evolution_service().evolve_from_execution(exec_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Execution or Crew not found for {exec_id}")
    return result
