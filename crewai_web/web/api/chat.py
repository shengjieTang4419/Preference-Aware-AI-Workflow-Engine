"""
对话式 Crew 生成 API（异步任务 + WebSocket 推送）
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, BackgroundTasks
from crewai_web.web.domain import ChatStreamRequest
from crewai_web.core.tools.websocket_manager import ws_manager
from crewai_web.web.services.chat_execution_log_service import execution_log_service
from crewai_web.web.services.crew_generation_pipeline import crew_generation_pipeline
from crewai_web.web.domain.execution_log import ExecutionLogCreate

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/generate-crew")
async def generate_crew(request: ChatStreamRequest, background_tasks: BackgroundTasks):
    """提交 Crew 生成任务（异步）"""
    # 创建执行记录
    execution = execution_log_service.create_execution(
        ExecutionLogCreate(scenario=request.scenario, doc_filenames=request.doc_filenames)
    )

    # 后台任务执行（委托给 service）
    background_tasks.add_task(
        crew_generation_pipeline.execute,
        execution.id,
        request.scenario,
        request.scene_id,
        request.doc_filenames,
        request.ocr_texts,
    )

    return {"execution_id": execution.id, "status": "pending"}


@router.websocket("/ws/{execution_id}")
async def websocket_endpoint(websocket: WebSocket, execution_id: str):
    """WebSocket 连接，用于接收任务进度推送"""
    await ws_manager.connect(execution_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(execution_id, websocket)
