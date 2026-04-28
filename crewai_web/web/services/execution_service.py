"""
执行元数据服务
职责：管理执行记录的 meta.json（CRUD + 状态更新）
"""
import json
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict
from uuid import uuid4
from crewai_web.web.config import EXECUTIONS_DIR
from crewai_web.web.domain.execution import ExecutionCreate, ExecutionOut, ExecutionStatus


def _exec_dir(exec_id: str) -> Path:
    return EXECUTIONS_DIR / exec_id


def _meta_path(exec_id: str) -> Path:
    return _exec_dir(exec_id) / "meta.json"


def list_executions() -> List[ExecutionOut]:
    """获取所有执行记录"""
    results = []
    for exec_dir in sorted(EXECUTIONS_DIR.iterdir()):
        if exec_dir.is_dir():
            meta = _load_meta(exec_dir.name)
            if meta:
                results.append(ExecutionOut(**meta))
    # 按时间倒序
    results.sort(key=lambda x: x.created_at, reverse=True)
    return results


def get_execution(exec_id: str) -> Optional[ExecutionOut]:
    """获取单个执行记录"""
    meta = _load_meta(exec_id)
    if not meta:
        return None
    return ExecutionOut(**meta)


def _load_meta(exec_id: str) -> Optional[Dict]:
    """加载 meta.json"""
    path = _meta_path(exec_id)
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_execution(create: ExecutionCreate) -> ExecutionOut:
    """创建执行记录，初始化目录结构"""
    exec_id = datetime.now().strftime("%Y%m%d_%H%M%S_") + uuid4().hex[:8]
    exec_dir = _exec_dir(exec_id)
    exec_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建 outputs 子目录
    outputs_dir = exec_dir / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    
    # 如果 output_dir 是相对路径，转为绝对路径
    output_dir = Path(create.output_dir).expanduser()
    if not output_dir.is_absolute():
        output_dir = exec_dir / "outputs"
    else:
        output_dir.mkdir(parents=True, exist_ok=True)
    
    now = datetime.utcnow().isoformat()
    meta = {
        "id": exec_id,
        "status": ExecutionStatus.PENDING.value,
        "requirement": create.requirement,
        "input_folder": create.input_folder,
        "crew_id": create.crew_id,
        "output_dir": str(output_dir),
        "inputs": create.inputs or {},  # 保存占位符值
        "logs_summary": None,
        "created_at": now,
        "started_at": None,
        "completed_at": None,
        "error_message": None,
    }
    
    _save_meta(exec_id, meta)
    
    return ExecutionOut(**meta)


def _save_meta(exec_id: str, meta: Dict) -> None:
    """保存 meta.json"""
    with open(_meta_path(exec_id), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)


def update_execution_status(
    exec_id: str,
    status: ExecutionStatus,
    error_message: Optional[str] = None,
    logs_summary: Optional[str] = None,
) -> Optional[ExecutionOut]:
    """更新执行状态"""
    meta = _load_meta(exec_id)
    if not meta:
        return None
    
    meta["status"] = status.value
    
    if status == ExecutionStatus.RUNNING and not meta.get("started_at"):
        meta["started_at"] = datetime.utcnow().isoformat()
    
    if status in (ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED):
        meta["completed_at"] = datetime.utcnow().isoformat()
    
    if error_message:
        meta["error_message"] = error_message
    
    if logs_summary:
        meta["logs_summary"] = logs_summary
    
    _save_meta(exec_id, meta)
    return ExecutionOut(**meta)


# ── 兼容层：重新导出已拆分的功能 ──────────────────────────

from crewai_web.web.services.execution_log_manager import append_log, get_logs
from crewai_web.web.services.execution_output_manager import (
    get_output_files,
    get_output_file_path,
    read_output_file,
)

__all__ = [
    # 元数据管理（本模块）
    "list_executions",
    "get_execution",
    "create_execution",
    "update_execution_status",
    # 日志管理（execution_log_manager）
    "append_log",
    "get_logs",
    # 输出文件管理（execution_output_manager）
    "get_output_files",
    "get_output_file_path",
    "read_output_file",
]
