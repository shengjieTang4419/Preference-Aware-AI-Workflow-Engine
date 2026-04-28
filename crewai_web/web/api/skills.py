"""
Skills API 接口
提供 Skills 的查询和管理功能
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel

from crewai_web.web.services.skills_service import get_skills_service
from crewai_web.web.services.skills_recommender import get_skills_recommender

router = APIRouter(prefix="/skills", tags=["skills"])


class SkillsRecommendRequest(BaseModel):
    """Skills 推荐请求"""
    role: str
    goal: str
    backstory: str
    task_context: str = ""


@router.get("/", response_model=List[Dict[str, Any]])
async def list_skills():
    """
    获取所有可用的 Skills
    
    Returns:
        Skills 列表
    """
    service = get_skills_service()
    return service.list_all_skills()


@router.get("/statistics", response_model=Dict[str, Any])
async def get_skills_statistics():
    """
    获取 Skills 统计信息
    
    Returns:
        统计信息
    """
    service = get_skills_service()
    return service.get_statistics()


@router.get("/{skill_name}", response_model=Dict[str, Any])
async def get_skill_detail(skill_name: str):
    """
    获取单个 Skill 的详细信息
    
    Args:
        skill_name: Skill 名称
    
    Returns:
        Skill 详细信息
    
    Raises:
        HTTPException: Skill 不存在时
    """
    service = get_skills_service()
    skill = service.get_skill_detail(skill_name)
    
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found")
    
    return skill


@router.get("/recommend/{role}", response_model=List[Dict[str, Any]])
async def get_recommended_skills(role: str):
    """
    根据角色推荐相关的 Skills（简单匹配）
    
    Args:
        role: Agent 角色
    
    Returns:
        推荐的 Skills 列表
    """
    service = get_skills_service()
    return service.get_skills_for_role(role)


@router.post("/ai-recommend", response_model=Dict[str, Any])
async def ai_recommend_skills(request: SkillsRecommendRequest):
    """
    使用 AI 智能推荐 Skills
    
    Args:
        request: 包含 Agent 信息的推荐请求
    
    Returns:
        AI 推荐的 Skills 配置
    """
    recommender = get_skills_recommender()
    skills_config = await recommender.recommend_for_agent(
        role=request.role,
        goal=request.goal,
        backstory=request.backstory,
        task_context=request.task_context
    )
    return skills_config
