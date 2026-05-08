"""
WebSocket 连接管理器 - 用于推送任务进度
"""
import asyncio
import json
import logging
from typing import Dict, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """WebSocket 连接管理器"""
    
    def __init__(self):
        # execution_id -> set of websockets
        self.connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()
    
    async def connect(self, execution_id: str, websocket: WebSocket):
        """注册 WebSocket 连接"""
        await websocket.accept()
        
        async with self._lock:
            if execution_id not in self.connections:
                self.connections[execution_id] = set()
            self.connections[execution_id].add(websocket)
        
        logger.info(f"WebSocket connected for execution {execution_id}")
    
    async def disconnect(self, execution_id: str, websocket: WebSocket):
        """移除 WebSocket 连接"""
        async with self._lock:
            if execution_id in self.connections:
                self.connections[execution_id].discard(websocket)
                if not self.connections[execution_id]:
                    del self.connections[execution_id]
        
        logger.info(f"WebSocket disconnected for execution {execution_id}")
    
    async def send_progress(self, execution_id: str, message: str, step: int = None, total: int = None, status: str = "running"):
        """向指定 execution 的所有连接推送进度"""
        if execution_id not in self.connections:
            return  # 没有连接，不推送
        
        event = {
            "type": "progress",
            "message": message,
            "status": status
        }
        
        if step is not None and total is not None:
            event["step"] = step
            event["total"] = total
            event["percentage"] = int((step / total) * 100)
        
        # 推送给所有连接
        disconnected = set()
        for ws in self.connections[execution_id]:
            try:
                await ws.send_json(event)
            except Exception as e:
                logger.error(f"Failed to send to websocket: {e}")
                disconnected.add(ws)
        
        # 清理断开的连接
        if disconnected:
            async with self._lock:
                self.connections[execution_id] -= disconnected
    
    async def send_complete(self, execution_id: str, result: dict):
        """推送完成消息"""
        await self._send_event(execution_id, {"type": "complete", "result": result})
    
    async def send_error(self, execution_id: str, error_message: str):
        """推送错误消息"""
        await self._send_event(execution_id, {"type": "error", "message": error_message})
    
    async def _send_event(self, execution_id: str, event: dict):
        """内部方法：发送事件"""
        if execution_id not in self.connections:
            return
        
        disconnected = set()
        for ws in self.connections[execution_id]:
            try:
                await ws.send_json(event)
            except Exception:
                disconnected.add(ws)
        
        if disconnected:
            async with self._lock:
                self.connections[execution_id] -= disconnected


# 全局单例
ws_manager = WebSocketManager()
