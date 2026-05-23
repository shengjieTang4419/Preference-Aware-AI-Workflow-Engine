"""创作 API — 薄路由层

POST /api/creativity/execute    执行创作任务
GET  /api/creativity/artifacts/{execution_id}  获取制品详情
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from crewai_web.web.api.deps import get_optional_user_id
from crewai_web.web.domain.creativity import (
    CreativityExecuteRequest,
    CreativityExecuteResponse,
    ArtifactOut,
)
from crewai_web.web.services import creativity_service

router = APIRouter(prefix="/creativity", tags=["creativity"])


@router.post("/execute", response_model=CreativityExecuteResponse)
async def execute_creative_task(
    req: CreativityExecuteRequest,
    user_id: Optional[int] = Depends(get_optional_user_id),
):
    """执行创作任务"""
    return await creativity_service.execute_creative_task(req, user_id)


@router.get("/artifacts/{execution_id}", response_model=ArtifactOut)
async def get_artifact(execution_id: str):
    """获取制品详情（兼容旧 Crew 执行记录）"""
    # 先查新的 creative_artifacts 表
    artifact = await creativity_service.get_artifact_by_execution_id(execution_id)
    if artifact:
        return artifact

    # 兼容旧的 Crew 执行记录
    artifact = _load_legacy_execution(execution_id)
    if artifact:
        return artifact

    raise HTTPException(status_code=404, detail="执行记录不存在")


def _load_legacy_execution(execution_id: str) -> Optional[ArtifactOut]:
    """从旧的 executions 目录加载数据，转换为 ArtifactOut 格式"""
    import json
    from pathlib import Path
    from datetime import datetime
    from crewai_web.web.config import EXECUTIONS_DIR

    exec_dir = EXECUTIONS_DIR / execution_id
    meta_file = exec_dir / "meta.json"
    if not meta_file.exists():
        return None

    with open(meta_file, "r", encoding="utf-8") as f:
        meta = json.load(f)

    # 读取执行日志
    log_file = exec_dir / "execution.log"
    log_content = ""
    if log_file.exists():
        with open(log_file, "r", encoding="utf-8") as f:
            log_content = f.read()

    # 收集输出文件
    output_files = []
    outputs_dir = exec_dir / "outputs"
    if outputs_dir.exists():
        for f in sorted(outputs_dir.rglob("*")):
            if f.is_file():
                output_files.append(str(f.relative_to(exec_dir)))

    # 从 logs_summary 提取预览文本
    preview = meta.get("logs_summary", "")
    if len(preview) > 2000:
        preview = preview[:2000]

    # 解析时间
    created_at = datetime.fromisoformat(meta["created_at"]) if meta.get("created_at") else datetime.utcnow()
    completed_at = datetime.fromisoformat(meta["completed_at"]) if meta.get("completed_at") else None

    # 状态映射
    status_map = {"completed": "completed", "running": "running", "failed": "failed", "pending": "pending"}
    status = status_map.get(meta.get("status", ""), "completed")

    return ArtifactOut(
        id=0,  # 旧数据无自增 ID
        execution_id=execution_id,
        scene_id="document",  # 旧执行默认为文档类型
        title=meta.get("requirement", "Crew 执行结果"),
        description=f"Crew: {meta.get('crew_id', '')}",
        output_type="markdown",
        output_dir=meta.get("output_dir"),
        output_files=output_files,
        preview_text=preview,
        status=status,
        error_message=meta.get("error_message"),
        created_at=created_at,
        completed_at=completed_at,
    )
