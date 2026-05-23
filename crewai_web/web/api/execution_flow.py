"""执行流程 API — 提供完整的执行流程数据

GET /api/executions/{exec_id}/flow  获取完整流程数据（任务、智能体、依赖关系）
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
import json
from pathlib import Path

from crewai_web.web.config import (
    EXECUTIONS_DIR,
    CREWS_DIR,
    TASKS_DIR,
    AGENTS_DIR,
)

router = APIRouter(prefix="/executions", tags=["execution-flow"])


def _read_json(path: Path) -> Optional[dict]:
    """读取 JSON 文件，不存在则返回 None"""
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_all_agents() -> dict[str, dict]:
    """加载所有 agent 文件"""
    agents = {}
    if not AGENTS_DIR.exists():
        return agents
    for f in sorted(AGENTS_DIR.glob("agent_*.json")):
        data = _read_json(f)
        if data and "id" in data:
            agents[data["id"]] = data
    return agents


def _load_all_tasks() -> dict[str, dict]:
    """加载所有 task 文件"""
    tasks = {}
    if not TASKS_DIR.exists():
        return tasks
    for f in sorted(TASKS_DIR.glob("task_*.json")):
        data = _read_json(f)
        if data and "id" in data:
            tasks[data["id"]] = data
    return tasks


def _load_all_crews() -> dict[str, dict]:
    """加载所有 crew 文件"""
    crews = {}
    if not CREWS_DIR.exists():
        return crews
    for f in sorted(CREWS_DIR.glob("crew_*.json")):
        data = _read_json(f)
        if data and "id" in data:
            crews[data["id"]] = data
    return crews


@router.get("/{exec_id}/flow")
def get_execution_flow(exec_id: str):
    """获取执行流程完整数据，包括任务、智能体、依赖关系和执行策略"""

    # 1. 读取执行记录
    exec_dir = EXECUTIONS_DIR / exec_id
    meta_file = exec_dir / "meta.json"
    meta = _read_json(meta_file)
    if not meta:
        raise HTTPException(status_code=404, detail=f"执行记录 '{exec_id}' 不存在")

    crew_id = meta.get("crew_id", "")
    if not crew_id:
        raise HTTPException(status_code=400, detail="执行记录缺少 crew_id")

    # 2. 读取 crew 数据
    crew_data = _load_all_crews().get(crew_id)
    if not crew_data:
        # 尝试从文件名匹配
        crew_file = CREWS_DIR / f"crew_{crew_id}.json"
        crew_data = _read_json(crew_file)
    if not crew_data:
        raise HTTPException(status_code=404, detail=f"Crew '{crew_id}' 不存在")

    # 3. 加载所有 agents 和 tasks
    all_agents = _load_all_agents()
    all_tasks = _load_all_tasks()

    # 4. 构建任务列表（按 crew 中的顺序）
    task_ids = crew_data.get("task_ids", [])
    agent_model_assignments = crew_data.get("agent_model_assignments", {})

    tasks_out = []
    for task_id in task_ids:
        task_data = all_tasks.get(task_id)
        if not task_data:
            # 尝试从文件名匹配
            task_file = TASKS_DIR / f"task_{task_id}.json"
            task_data = _read_json(task_file)
        if not task_data:
            continue

        agent_id = task_data.get("agent_id", "")
        agent_data = all_agents.get(agent_id)
        if not agent_data:
            agent_file = AGENTS_DIR / f"agent_{agent_id}.json"
            agent_data = _read_json(agent_file)

        # 获取模型等级
        model_tier = agent_model_assignments.get(agent_id, "basic")

        # 计算任务状态（基于执行整体状态推断）
        task_status = _infer_task_status(meta, task_ids.index(task_id), len(task_ids))

        task_out = {
            "id": task_data.get("id", task_id),
            "name": task_data.get("name", task_id),
            "description": task_data.get("description", ""),
            "expected_output": task_data.get("expected_output", ""),
            "agent_id": agent_id,
            "agent_name": agent_data.get("name", agent_id) if agent_data else agent_id,
            "agent_role": agent_data.get("role", "") if agent_data else "",
            "agent_goal": agent_data.get("goal", "") if agent_data else "",
            "agent_backstory": agent_data.get("backstory", "") if agent_data else "",
            "model_tier": model_tier,
            "context_task_ids": task_data.get("context_task_ids", []),
            "async_execution": task_data.get("async_execution", False),
            "status": task_status,
            "index": task_ids.index(task_id),
        }
        tasks_out.append(task_out)

    # 5. 构建 agents 列表
    agent_ids = crew_data.get("agent_ids", [])
    agents_out = []
    for agent_id in agent_ids:
        agent_data = all_agents.get(agent_id)
        if not agent_data:
            agent_file = AGENTS_DIR / f"agent_{agent_id}.json"
            agent_data = _read_json(agent_file)
        if not agent_data:
            continue

        model_tier = agent_model_assignments.get(agent_id, "basic")
        # 找到该 agent 负责的任务
        assigned_tasks = [
            t["id"] for t in tasks_out if t["agent_id"] == agent_id
        ]

        agent_out = {
            "id": agent_data.get("id", agent_id),
            "name": agent_data.get("name", agent_id),
            "role": agent_data.get("role", ""),
            "goal": agent_data.get("goal", ""),
            "backstory": agent_data.get("backstory", ""),
            "llm_key": agent_data.get("llm_key", "default"),
            "model_tier": model_tier,
            "assigned_tasks": assigned_tasks,
        }
        agents_out.append(agent_out)

    # 6. 构建 edges（依赖关系）
    edges_out = []
    for task in tasks_out:
        for dep_id in task["context_task_ids"]:
            # 确保依赖任务在当前 crew 中
            if any(t["id"] == dep_id for t in tasks_out):
                edges_out.append({
                    "source": dep_id,
                    "target": task["id"],
                    "type": "dependency",
                })

    # 7. 构建完整流程数据
    flow_data = {
        "execution": {
            "id": meta.get("id", exec_id),
            "status": meta.get("status", "unknown"),
            "requirement": meta.get("requirement", ""),
            "crew_id": crew_id,
            "created_at": meta.get("created_at", ""),
            "started_at": meta.get("started_at", ""),
            "completed_at": meta.get("completed_at", ""),
            "error_message": meta.get("error_message"),
        },
        "crew": {
            "id": crew_data.get("id", crew_id),
            "name": crew_data.get("name", crew_id),
            "description": crew_data.get("description", ""),
            "process_type": crew_data.get("process_type", "sequential"),
            "agent_model_assignments": agent_model_assignments,
        },
        "tasks": tasks_out,
        "agents": agents_out,
        "edges": edges_out,
    }

    return flow_data


def _infer_task_status(meta: dict, task_index: int, total_tasks: int) -> str:
    """根据执行整体状态推断单个任务状态"""
    exec_status = meta.get("status", "unknown")

    if exec_status == "completed":
        return "completed"
    elif exec_status == "failed":
        # 最后一个任务标记为 failed，其余 completed
        if task_index == total_tasks - 1:
            return "failed"
        return "completed"
    elif exec_status == "running":
        # 简单推断：假设按顺序执行
        return "running"
    else:
        return "pending"
