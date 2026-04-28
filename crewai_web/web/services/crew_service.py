import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from crewai_web.web.config import CREWS_DIR
from crewai_web.web.domain.crew import CrewCreate, CrewUpdate, CrewOut


def _crew_path(crew_id: str) -> Path:
    return CREWS_DIR / f"crew_{crew_id}.json"


def _load_crew_file(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def list_crews() -> List[CrewOut]:
    """获取所有 Crew 配置列表"""
    results = []
    for f in sorted(CREWS_DIR.glob("crew_*.json")):
        data = _load_crew_file(f)
        if data:
            results.append(CrewOut(**data))
    return results


def get_crew(crew_id: str) -> Optional[CrewOut]:
    """获取单个 Crew 配置"""
    data = _load_crew_file(_crew_path(crew_id))
    if not data:
        return None
    return CrewOut(**data)


def create_crew(crew: CrewCreate) -> CrewOut:
    """创建 Crew 配置"""
    path = _crew_path(crew.name)
    if path.exists():
        raise ValueError(f"Crew '{crew.name}' already exists")
    
    now = datetime.utcnow()
    data = {
        "id": crew.name,
        "name": crew.name,
        "description": crew.description,
        "agent_ids": crew.agent_ids,
        "task_ids": crew.task_ids,
        "process_type": crew.process_type,
        "agent_model_assignments": crew.agent_model_assignments or {},
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return CrewOut(**data)


def update_crew(crew_id: str, update: CrewUpdate) -> Optional[CrewOut]:
    """更新 Crew 配置"""
    path = _crew_path(crew_id)
    data = _load_crew_file(path)
    if not data:
        return None
    
    for field, value in update.model_dump(exclude_unset=True).items():
        if value is not None:
            data[field] = value
    
    data["updated_at"] = datetime.utcnow().isoformat()
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return CrewOut(**data)


def delete_crew(crew_id: str) -> bool:
    """删除 Crew 配置，返回是否成功"""
    path = _crew_path(crew_id)
    if not path.exists():
        return False
    path.unlink()
    return True
