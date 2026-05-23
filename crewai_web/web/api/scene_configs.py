from fastapi import APIRouter, HTTPException
from typing import List

from crewai_web.web.domain.scene_config import (
    SceneConfigCreate, SceneConfigUpdate, SceneConfigOut,
)
from crewai_web.web.services import scene_config_service

router = APIRouter(prefix="/scene-configs", tags=["scene-configs"])


@router.get("", response_model=List[SceneConfigOut])
async def list_configs():
    """获取场景配置列表"""
    return await scene_config_service.list_configs()


@router.get("/all", response_model=List[SceneConfigOut])
async def list_all_configs():
    """获取全部配置（含禁用/隐藏，管理后台用）"""
    return await scene_config_service.list_configs(enabled_only=False, visible_only=False)


@router.get("/{config_id}", response_model=SceneConfigOut)
async def get_config(config_id: str):
    """获取单个配置"""
    config = await scene_config_service.get_config(config_id)
    if not config:
        raise HTTPException(status_code=404, detail=f"场景配置 '{config_id}' 不存在")
    return config


@router.post("", response_model=SceneConfigOut, status_code=201)
async def create_config(req: SceneConfigCreate):
    """创建场景配置"""
    try:
        return await scene_config_service.create_config(req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{config_id}", response_model=SceneConfigOut)
async def update_config(config_id: str, req: SceneConfigUpdate):
    """更新场景配置"""
    config = await scene_config_service.update_config(config_id, req)
    if not config:
        raise HTTPException(status_code=404, detail=f"场景配置 '{config_id}' 不存在")
    return config


@router.delete("/{config_id}", status_code=204)
async def delete_config(config_id: str):
    """删除场景配置"""
    success = await scene_config_service.delete_config(config_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"场景配置 '{config_id}' 不存在")
