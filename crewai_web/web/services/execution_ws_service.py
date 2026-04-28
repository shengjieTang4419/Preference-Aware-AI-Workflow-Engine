"""
执行 WebSocket 服务
职责：管理 WebSocket 连接、实时推送执行日志
"""
import asyncio
import logging
from fastapi import WebSocket, WebSocketDisconnect
from crewai_web.web.services import execution_service

logger = logging.getLogger(__name__)


class ExecutionWebSocketService:
    """执行 WebSocket 实时日志推送服务"""

    async def handle_connection(self, websocket: WebSocket, exec_id: str):
        """处理 WebSocket 连接"""
        exec_record = execution_service.get_execution(exec_id)
        if not exec_record:
            await websocket.close(code=1008, reason=f"Execution '{exec_id}' not found")
            return

        await websocket.accept()

        try:
            # 发送当前状态
            await websocket.send_json({"type": "status", "status": exec_record.status})

            # 如果执行已完成，发送完整日志后关闭
            if exec_record.status in ("completed", "failed", "cancelled"):
                logs = execution_service.get_logs(exec_id)
                await websocket.send_json({"type": "logs", "content": logs})
                await websocket.close()
                return

            # 对于正在执行的，定期轮询日志增量
            last_size = 0
            while True:
                await asyncio.sleep(1)

                exec_record = execution_service.get_execution(exec_id)
                if not exec_record:
                    break

                logs = execution_service.get_logs(exec_id)
                if len(logs) > last_size:
                    new_content = logs[last_size:]
                    await websocket.send_json({"type": "log_delta", "content": new_content})
                    last_size = len(logs)

                if exec_record.status in ("completed", "failed", "cancelled"):
                    await websocket.send_json({"type": "status", "status": exec_record.status})
                    break

        except WebSocketDisconnect:
            pass
        finally:
            try:
                await websocket.close()
            except Exception:
                pass


_ws_service = None


def get_execution_ws_service() -> ExecutionWebSocketService:
    global _ws_service
    if _ws_service is None:
        _ws_service = ExecutionWebSocketService()
    return _ws_service
