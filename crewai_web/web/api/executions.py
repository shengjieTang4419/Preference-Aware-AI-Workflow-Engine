from fastapi import APIRouter, HTTPException, WebSocket, BackgroundTasks
from fastapi.responses import FileResponse
from typing import List
from crewai_web.web.domain.execution import ExecutionCreate, ExecutionOut, ExecutionFileTree
from crewai_web.web.services import execution_service, crew_service
from crewai_web.web.runner.crew_runner import run_crew_async
from crewai_web.web.services.execution_ws_service import get_execution_ws_service

router = APIRouter(prefix="/executions", tags=["executions"])


@router.get("", response_model=List[ExecutionOut])
def list_executions():
    """获取执行历史列表"""
    return execution_service.list_executions()


@router.get("/{exec_id}", response_model=ExecutionOut)
def get_execution(exec_id: str):
    """获取执行详情"""
    exec_record = execution_service.get_execution(exec_id)
    if not exec_record:
        raise HTTPException(status_code=404, detail=f"Execution '{exec_id}' not found")
    return exec_record


@router.post("", response_model=ExecutionOut, status_code=201)
def create_execution(create: ExecutionCreate, background_tasks: BackgroundTasks):
    """提交新执行，立即返回并在后台启动"""
    crew = crew_service.get_crew(create.crew_id)
    if not crew:
        raise HTTPException(status_code=400, detail=f"Crew '{create.crew_id}' not found")

    exec_record = execution_service.create_execution(create)

    background_tasks.add_task(
        run_crew_async,
        exec_record.id,
        exec_record.requirement,
        exec_record.input_folder,
        exec_record.crew_id,
        exec_record.output_dir,
    )
    return exec_record


@router.get("/{exec_id}/logs")
def get_execution_logs(exec_id: str):
    """获取执行日志内容"""
    if not execution_service.get_execution(exec_id):
        raise HTTPException(status_code=404, detail=f"Execution '{exec_id}' not found")
    logs = execution_service.get_logs(exec_id)
    return {"execution_id": exec_id, "content": logs}


@router.get("/{exec_id}/files", response_model=ExecutionFileTree)
def get_execution_files(exec_id: str):
    """获取输出文件树"""
    exec_record = execution_service.get_execution(exec_id)
    if not exec_record:
        raise HTTPException(status_code=404, detail=f"Execution '{exec_id}' not found")
    files = execution_service.get_output_files(exec_id)
    return {"execution_id": exec_id, "output_dir": exec_record.output_dir, "files": files}


@router.get("/{exec_id}/files/download")
def download_execution_file(exec_id: str, file_path: str):
    """下载输出文件"""
    full_path = execution_service.get_output_file_path(exec_id, file_path)
    if not full_path:
        raise HTTPException(status_code=404, detail=f"File '{file_path}' not found")
    return FileResponse(path=str(full_path), filename=full_path.name, media_type="application/octet-stream")


@router.get("/{exec_id}/files/content")
def get_execution_file_content(exec_id: str, file_path: str):
    """读取输出文件内容"""
    content = execution_service.read_output_file(exec_id, file_path)
    if content is None:
        raise HTTPException(status_code=404, detail=f"File '{file_path}' not found")
    return {"execution_id": exec_id, "file_path": file_path, "content": content}


@router.websocket("/{exec_id}/ws")
async def execution_websocket(websocket: WebSocket, exec_id: str):
    """WebSocket 实时日志流"""
    await get_execution_ws_service().handle_connection(websocket, exec_id)
