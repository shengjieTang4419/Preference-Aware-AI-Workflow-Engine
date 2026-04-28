"""
执行日志查询 API
"""
from fastapi import APIRouter, HTTPException
from typing import List
from crewai_web.web.services.chat_execution_log_service import execution_log_service
from crewai_web.web.domain.execution_log import ExecutionLog

router = APIRouter(prefix="/execution-logs", tags=["execution-logs"])


@router.get("/", response_model=List[ExecutionLog])
async def list_execution_logs(limit: int = 50):
    """
    获取执行日志列表
    
    Args:
        limit: 返回数量限制，默认50
    
    Returns:
        执行日志列表（按时间倒序）
    """
    return execution_log_service.list_executions(limit=limit)


@router.get("/{execution_id}", response_model=ExecutionLog)
async def get_execution_log(execution_id: str):
    """
    获取单个执行日志详情
    
    Args:
        execution_id: 执行ID
    
    Returns:
        执行日志详情（包含完整日志）
    """
    execution = execution_log_service.get_execution(execution_id)
    
    if not execution:
        raise HTTPException(status_code=404, detail=f"Execution not found: {execution_id}")
    
    return execution


@router.get("/{execution_id}/status")
async def get_execution_status(execution_id: str):
    """
    获取执行状态（轻量级接口，不返回完整日志）
    
    Args:
        execution_id: 执行ID
    
    Returns:
        执行状态摘要
    """
    execution = execution_log_service.get_execution(execution_id)
    
    if not execution:
        raise HTTPException(status_code=404, detail=f"Execution not found: {execution_id}")
    
    return {
        "id": execution.id,
        "status": execution.status,
        "scenario": execution.scenario,
        "start_time": execution.start_time,
        "end_time": execution.end_time,
        "topic": execution.topic,
        "crew_id": execution.crew_id,
        "error_message": execution.error_message,
        "log_count": len(execution.logs)
    }
