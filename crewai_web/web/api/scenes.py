from fastapi import APIRouter
from typing import List

from crewai_web.web.domain.scene import SceneOut
from crewai_web.web.services import scene_service

router = APIRouter(prefix="/scenes", tags=["scenes"])


@router.get("", response_model=List[SceneOut])
async def list_scenes():
    """获取场景卡片列表"""
    return await scene_service.list_scenes()
