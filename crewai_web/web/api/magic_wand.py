"""魔法棒API — 制品Skill匹配

POST /api/magic-wand/match — 匹配制品生成所需的Skills
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

from crewai_web.web.services import magic_wand_service
from crewai_web.web.services.scene_config_service import get_config

router = APIRouter(prefix="/magic-wand", tags=["magic-wand"])


class MatchRequest(BaseModel):
    """匹配请求"""
    scene_id: str = Field(..., description="场景ID")
    user_input: str = Field(..., description="用户输入")


class SkillMatch(BaseModel):
    """匹配到的Skill"""
    name: str
    output_type: str = ""
    description: str = ""


class MatchResponse(BaseModel):
    """匹配响应"""
    scene_id: str
    skills: List[SkillMatch]
    source: str  # "preset" | "scanned" | "inferred"


@router.post("/match", response_model=MatchResponse)
async def match_skills(req: MatchRequest):
    """魔法棒: 匹配制品生成所需的Skills"""
    # 获取场景配置
    config = await get_config(req.scene_id)
    scene_artifact_skills = None
    if config and config.artifact_skills:
        scene_artifact_skills = config.artifact_skills

    # 匹配
    matched = await magic_wand_service.match_artifact_skills(
        scene_id=req.scene_id,
        user_input=req.user_input,
        scene_artifact_skills=scene_artifact_skills,
    )

    if not matched:
        return MatchResponse(
            scene_id=req.scene_id,
            skills=[],
            source="none",
        )

    # 判断来源
    if scene_artifact_skills:
        source = "preset"
    elif any(s.get("path", "").startswith("installed:") for s in matched):
        source = "scanned"
    else:
        source = "inferred"

    skills = [
        SkillMatch(
            name=s["name"],
            output_type=s.get("output_type", ""),
            description=s.get("metadata", {}).get("description", ""),
        )
        for s in matched
    ]

    return MatchResponse(
        scene_id=req.scene_id,
        skills=skills,
        source=source,
    )
