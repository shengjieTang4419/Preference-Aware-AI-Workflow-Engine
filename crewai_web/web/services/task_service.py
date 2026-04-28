import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from crewai_web.web.config import TASKS_DIR
from crewai_web.web.domain.task import TaskCreate, TaskUpdate, TaskOut


def _task_path(task_id: str) -> Path:
    return TASKS_DIR / f"task_{task_id}.json"


def _load_task_file(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def list_tasks() -> List[TaskOut]:
    """获取所有 Task 列表"""
    results = []
    for f in sorted(TASKS_DIR.glob("task_*.json")):
        data = _load_task_file(f)
        if data:
            results.append(TaskOut(**data))
    return results


def get_task(task_id: str) -> Optional[TaskOut]:
    """获取单个 Task"""
    data = _load_task_file(_task_path(task_id))
    if not data:
        return None
    return TaskOut(**data)


def create_task(task: TaskCreate) -> TaskOut:
    """创建 Task"""
    path = _task_path(task.name)
    if path.exists():
        raise ValueError(f"Task '{task.name}' already exists")
    
    now = datetime.utcnow()
    data = {
        "id": task.name,
        "name": task.name,
        "description": task.description,
        "expected_output": task.expected_output,
        "agent_id": task.agent_id,
        "context_task_ids": task.context_task_ids,
        "async_execution": task.async_execution,
        # 新增字段
        "topic": task.topic,
        "crew_id": task.crew_id,
        "execution_id": task.execution_id,
        "role_type": task.role_type,
        # 时间戳
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return TaskOut(**data)


def update_task(task_id: str, update: TaskUpdate) -> Optional[TaskOut]:
    """更新 Task"""
    path = _task_path(task_id)
    data = _load_task_file(path)
    if not data:
        return None
    
    for field, value in update.model_dump(exclude_unset=True).items():
        if value is not None:
            data[field] = value
    
    data["updated_at"] = datetime.utcnow().isoformat()
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return TaskOut(**data)


def delete_task(task_id: str) -> bool:
    """删除 Task，返回是否成功"""
    path = _task_path(task_id)
    if not path.exists():
        return False
    path.unlink()
    return True
