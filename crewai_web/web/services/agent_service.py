import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from crewai_web.web.config import AGENTS_DIR
from crewai_web.web.domain.agent import AgentCreate, AgentUpdate, AgentOut


def _agent_path(agent_id: str) -> Path:
    return AGENTS_DIR / f"agent_{agent_id}.json"


def _load_agent_file(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def list_agents() -> List[AgentOut]:
    """获取所有 Agent 列表"""
    results = []
    for f in sorted(AGENTS_DIR.glob("agent_*.json")):
        data = _load_agent_file(f)
        if data:
            results.append(AgentOut(**data))
    return results


def get_agent(agent_id: str) -> Optional[AgentOut]:
    """获取单个 Agent"""
    data = _load_agent_file(_agent_path(agent_id))
    if not data:
        return None
    return AgentOut(**data)


def create_agent(agent: AgentCreate) -> AgentOut:
    """创建 Agent"""
    path = _agent_path(agent.name)
    if path.exists():
        raise ValueError(f"Agent '{agent.name}' already exists")
    
    now = datetime.utcnow()
    data = {
        "id": agent.name,
        "name": agent.name,
        "role": agent.role,
        "goal": agent.goal,
        "backstory": agent.backstory,
        "allow_delegation": agent.allow_delegation,
        "max_execution_time": agent.max_execution_time,
        "llm_key": agent.llm_key,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return AgentOut(**data)


def update_agent(agent_id: str, update: AgentUpdate) -> Optional[AgentOut]:
    """更新 Agent"""
    path = _agent_path(agent_id)
    data = _load_agent_file(path)
    if not data:
        return None
    
    for field, value in update.model_dump(exclude_unset=True).items():
        if value is not None:
            data[field] = value
    
    data["updated_at"] = datetime.utcnow().isoformat()
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return AgentOut(**data)


def delete_agent(agent_id: str) -> bool:
    """删除 Agent，返回是否成功"""
    path = _agent_path(agent_id)
    if not path.exists():
        return False
    path.unlink()
    return True
