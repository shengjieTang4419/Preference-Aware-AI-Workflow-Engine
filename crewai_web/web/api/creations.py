from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional

from crewai_web.web.api.deps import get_optional_user_id
from crewai_web.web.domain.creation import CreationCreate, CreationOut
from crewai_web.web.services import creation_service

router = APIRouter(prefix="/creations", tags=["creations"])


@router.post("", response_model=CreationOut, status_code=201)
async def create_creation(req: CreationCreate, user_id: Optional[int] = Depends(get_optional_user_id)):
    """创建创作记录"""
    return await creation_service.create_creation(req, user_id)


@router.get("", response_model=List[CreationOut])
async def list_creations(user_id: Optional[int] = Depends(get_optional_user_id)):
    """获取我的创作记录"""
    return await creation_service.list_creations(user_id)


@router.get("/{creation_id}", response_model=CreationOut)
async def get_creation(creation_id: int):
    """获取创作详情"""
    creation = await creation_service.get_creation(creation_id)
    if not creation:
        raise HTTPException(status_code=404, detail="创作记录不存在")
    return creation
