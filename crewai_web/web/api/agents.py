from fastapi import APIRouter, HTTPException
from typing import List
from crewai_web.web.domain.agent import AgentCreate, AgentUpdate, AgentOut
from crewai_web.web.services import agent_service

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=List[AgentOut])
def list_agents():
    """获取所有 Agent 列表"""
    return agent_service.list_agents()


@router.get("/{agent_id}", response_model=AgentOut)
def get_agent(agent_id: str):
    """获取单个 Agent 详情"""
    agent = agent_service.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    return agent


@router.post("", response_model=AgentOut, status_code=201)
def create_agent(agent: AgentCreate):
    """创建新 Agent"""
    try:
        return agent_service.create_agent(agent)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{agent_id}", response_model=AgentOut)
def update_agent(agent_id: str, update: AgentUpdate):
    """更新 Agent"""
    agent = agent_service.update_agent(agent_id, update)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    return agent


@router.delete("/{agent_id}", status_code=204)
def delete_agent(agent_id: str):
    """删除 Agent"""
    success = agent_service.delete_agent(agent_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    return None
