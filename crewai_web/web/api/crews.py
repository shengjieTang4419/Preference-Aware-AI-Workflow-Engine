from fastapi import APIRouter, HTTPException
from typing import List
from crewai_web.web.domain.crew import CrewCreate, CrewUpdate, CrewOut
from crewai_web.web.services import crew_service
from crewai_web.web.services.placeholder_service import get_crew_placeholders

router = APIRouter(prefix="/crews", tags=["crews"])


@router.get("", response_model=List[CrewOut])
def list_crews():
    """获取所有 Crew 配置列表"""
    return crew_service.list_crews()


@router.get("/{crew_id}", response_model=CrewOut)
def get_crew(crew_id: str):
    """获取单个 Crew 配置详情"""
    crew = crew_service.get_crew(crew_id)
    if not crew:
        raise HTTPException(status_code=404, detail=f"Crew '{crew_id}' not found")
    return crew


@router.post("", response_model=CrewOut, status_code=201)
def create_crew(crew: CrewCreate):
    """创建新 Crew 配置"""
    try:
        return crew_service.create_crew(crew)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{crew_id}", response_model=CrewOut)
def update_crew(crew_id: str, update: CrewUpdate):
    """更新 Crew 配置"""
    crew = crew_service.update_crew(crew_id, update)
    if not crew:
        raise HTTPException(status_code=404, detail=f"Crew '{crew_id}' not found")
    return crew


@router.delete("/{crew_id}", status_code=204)
def delete_crew(crew_id: str):
    """删除 Crew 配置"""
    success = crew_service.delete_crew(crew_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Crew '{crew_id}' not found")
    return None


@router.get("/{crew_id}/placeholders", response_model=List[str])
def get_placeholders(crew_id: str):
    """获取 Crew 中所有的占位符"""
    try:
        return get_crew_placeholders(crew_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
