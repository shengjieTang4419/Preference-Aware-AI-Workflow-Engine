from fastapi import APIRouter, HTTPException
from typing import List
from crewai_web.web.domain.task import TaskCreate, TaskUpdate, TaskOut
from crewai_web.web.services import task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=List[TaskOut])
def list_tasks():
    """获取所有 Task 列表"""
    return task_service.list_tasks()


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: str):
    """获取单个 Task 详情"""
    task = task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")
    return task


@router.post("", response_model=TaskOut, status_code=201)
def create_task(task: TaskCreate):
    """创建新 Task"""
    try:
        return task_service.create_task(task)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{task_id}", response_model=TaskOut)
def update_task(task_id: str, update: TaskUpdate):
    """更新 Task"""
    task = task_service.update_task(task_id, update)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")
    return task


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: str):
    """删除 Task"""
    success = task_service.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")
    return None
