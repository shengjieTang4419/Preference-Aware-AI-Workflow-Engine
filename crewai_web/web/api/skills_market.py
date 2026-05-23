"""技能发现与管理 API"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from crewai_web.web.api.deps import get_optional_user_id
from crewai_web.web.services import skills_market_service

router = APIRouter(prefix="/skills-market", tags=["skills-market"])


@router.get("/discover")
async def discover_skills(q: str = "", limit: int = 20):
    """发现热门技能（来自 skills.sh）"""
    return await skills_market_service.discover_skills(query=q, limit=limit)


@router.get("/installed")
async def list_installed():
    """获取已安装技能列表"""
    return skills_market_service.list_installed()


@router.get("/installed/{skill_name}")
async def get_skill_detail(skill_name: str):
    """获取单个已安装技能详情"""
    skill = skills_market_service.get_skill_detail(skill_name)
    if not skill:
        raise HTTPException(status_code=404, detail=f"技能 '{skill_name}' 未安装")
    return skill


@router.post("/install")
async def install_skill(body: dict, user_id: Optional[int] = Depends(get_optional_user_id)):
    """安装技能并生成 AI 说明"""
    package = body.get("package")
    if not package:
        raise HTTPException(status_code=400, detail="缺少 package 参数")

    try:
        return await skills_market_service.install_skill(package, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/installed/{skill_name}")
async def uninstall_skill(skill_name: str):
    """卸载技能"""
    success = skills_market_service.uninstall_skill(skill_name)
    if not success:
        raise HTTPException(status_code=404, detail=f"技能 '{skill_name}' 未安装")
    return {"status": "ok", "message": f"技能 '{skill_name}' 已卸载"}
