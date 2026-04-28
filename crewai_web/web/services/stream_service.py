"""
流式 Crew 生成服务
职责：SSE 流式日志推送、Crew 生成编排
"""
import asyncio
import logging
import json
from typing import Optional, AsyncGenerator

from crewai_web.web.config import UPLOAD_DIR
from crewai_web.web.services.ai_generator_service import ai_generator_service
from crewai_web.web.services.chat_execution_log_service import execution_log_service
from crewai_web.web.domain.execution_log import ExecutionLogCreate, ExecutionStatus

logger = logging.getLogger(__name__)


class StreamLogHandler(logging.Handler):
    """自定义日志处理器，将日志推送到队列并持久化"""

    def __init__(self, queue: asyncio.Queue, execution_id: str):
        super().__init__()
        self.queue = queue
        self.execution_id = execution_id

    def emit(self, record):
        try:
            msg = self.format(record)

            # 持久化到文件
            execution_log_service.add_log(
                self.execution_id,
                record.levelname,
                msg,
                record.name
            )

            # 非阻塞放入队列
            asyncio.create_task(self.queue.put({
                "type": "log",
                "level": record.levelname,
                "message": msg,
                "timestamp": record.created
            }))
        except Exception:
            self.handleError(record)


MONITORED_LOGGERS = [
    "crewai_web.core.ai.client",
    "crewai_web.web.services.ai_generator_service",
    "crewai_web.web.services.task_generator",
    "crewai_web.web.services.agent_generator",
]


class CrewStreamService:
    """流式 Crew 生成服务"""

    def _sse(self, data: dict) -> str:
        """格式化为 SSE 消息"""
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

    def _resolve_context(self, context: Optional[str], doc_filename: Optional[str]) -> tuple[Optional[str], Optional[str]]:
        """解析文档上下文，返回 (context, error)"""
        if not doc_filename:
            return context, None

        doc_path = UPLOAD_DIR / doc_filename
        if not doc_path.exists():
            return context, f"文档不存在: {doc_filename}"

        doc_content = doc_path.read_text(encoding="utf-8")
        doc_header = f"=== 参考文档: {doc_filename} ===\n{doc_content}\n=== 文档结束 ==="
        merged = f"{doc_header}\n\n{context}" if context else doc_header
        logger.info(f"Loaded doc '{doc_filename}' ({len(doc_content)} chars) as context")
        return merged, None

    async def generate_stream(
        self,
        scenario: str,
        context: Optional[str] = None,
        doc_filename: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """生成 Crew 并流式推送日志"""
        # 创建执行记录
        execution = execution_log_service.create_execution(
            ExecutionLogCreate(
                scenario=scenario,
                context=context,
                doc_filename=doc_filename
            )
        )
        execution_id = execution.id

        log_queue: asyncio.Queue = asyncio.Queue()

        # 创建日志处理器
        handler = StreamLogHandler(log_queue, execution_id)
        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter('[%(name)s] %(message)s'))

        # 挂载到相关 logger
        monitored = [logging.getLogger(name) for name in MONITORED_LOGGERS]
        for lg in monitored:
            lg.addHandler(handler)

        try:
            # 解析文档上下文
            context, doc_error = self._resolve_context(context, doc_filename)
            if doc_error:
                yield self._sse({"type": "error", "message": doc_error})
                return

            # 更新状态
            execution_log_service.update_status(execution_id, ExecutionStatus.RUNNING)
            yield self._sse({"type": "start", "message": "开始生成 Crew...", "execution_id": execution_id})

            # 启动生成任务（传入 execution_id）
            generation_task = asyncio.create_task(
                ai_generator_service.generate_crew_from_scenario(
                    scenario, 
                    context,
                    execution_id=execution_id
                )
            )

            # 持续推送日志
            while not generation_task.done():
                try:
                    log_msg = await asyncio.wait_for(log_queue.get(), timeout=0.5)
                    yield self._sse(log_msg)
                except asyncio.TimeoutError:
                    yield self._sse({"type": "heartbeat"})

            # 获取结果
            error = None
            result = None
            try:
                result = await generation_task
            except Exception as e:
                error = str(e)
                logger.error(f"Generation failed: {e}")
                execution_log_service.set_error(execution_id, error)

            # 推送剩余日志
            while not log_queue.empty():
                log_msg = await log_queue.get()
                yield self._sse(log_msg)

            # 发送最终结果
            if error:
                execution_log_service.update_status(execution_id, ExecutionStatus.FAILED)
                yield self._sse({"type": "error", "message": error, "execution_id": execution_id})
            else:
                execution_log_service.set_result(execution_id, result)
                execution_log_service.update_status(execution_id, ExecutionStatus.COMPLETED)
                yield self._sse({"type": "complete", "result": result, "execution_id": execution_id})

        finally:
            for lg in monitored:
                lg.removeHandler(handler)


_stream_service: Optional[CrewStreamService] = None


def get_stream_service() -> CrewStreamService:
    global _stream_service
    if _stream_service is None:
        _stream_service = CrewStreamService()
    return _stream_service
