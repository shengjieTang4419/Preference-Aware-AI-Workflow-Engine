"""
对话式 Crew 生成 API（同步 + SSE 流式）
"""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from crewai_web.web.services.ai_generator_service import ai_generator_service
from crewai_web.web.services.stream_service import get_stream_service

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """对话请求"""
    scenario: str
    context: Optional[str] = None


class ChatStreamRequest(BaseModel):
    """流式对话请求"""
    scenario: str
    context: Optional[str] = None
    doc_filename: Optional[str] = None


class ChatResponse(BaseModel):
    """对话响应"""
    topic: str
    crew_id: str
    agent_ids: list[str]
    task_ids: list[str]
    summary: str


@router.post("/generate-crew", response_model=ChatResponse)
async def generate_crew_from_chat(request: ChatRequest):
    """从对话生成 Crew"""
    result = await ai_generator_service.generate_crew_from_scenario(
        scenario=request.scenario,
        user_context=request.context
    )
    return ChatResponse(**result)


@router.post("/generate-crew-stream")
async def generate_crew_stream(request: ChatStreamRequest):
    """流式生成 Crew（SSE）"""
    return StreamingResponse(
        get_stream_service().generate_stream(request.scenario, request.context, request.doc_filename),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
