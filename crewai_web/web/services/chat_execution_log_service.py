"""
Chat 流式生成执行日志服务
职责：管理 /chat/generate-crew-stream 的执行日志（独立于 Crew 执行系统）
存储位置：storage/execution_logs/
"""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from crewai_web.web.domain.execution_log import (
    ExecutionLog, 
    ExecutionStatus, 
    LogEntry,
    ExecutionLogCreate
)

logger = logging.getLogger(__name__)


class ExecutionLogService:
    """执行日志服务"""
    
    def __init__(self, storage_dir: Path = None):
        if storage_dir is None:
            storage_dir = Path("/workspaces/one_person_company/storage/execution_logs")
        
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"ExecutionLogService initialized: {self.storage_dir}")
    
    def _get_log_path(self, execution_id: str) -> Path:
        """获取日志文件路径"""
        return self.storage_dir / f"{execution_id}.json"
    
    def create_execution(self, data: ExecutionLogCreate) -> ExecutionLog:
        """创建新的执行记录"""
        execution_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        
        execution = ExecutionLog(
            id=execution_id,
            scenario=data.scenario,
            status=ExecutionStatus.PENDING,
            start_time=datetime.now()
        )
        
        self._save(execution)
        logger.info(f"Created execution log: {execution_id}")
        return execution
    
    def get_execution(self, execution_id: str) -> Optional[ExecutionLog]:
        """获取执行记录"""
        log_path = self._get_log_path(execution_id)
        
        if not log_path.exists():
            return None
        
        try:
            data = json.loads(log_path.read_text(encoding="utf-8"))
            return ExecutionLog(**data)
        except Exception as e:
            logger.error(f"Failed to load execution log {execution_id}: {e}")
            return None
    
    def update_status(self, execution_id: str, status: ExecutionStatus):
        """更新执行状态"""
        execution = self.get_execution(execution_id)
        if not execution:
            logger.warning(f"Execution not found: {execution_id}")
            return
        
        execution.status = status
        
        if status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED]:
            execution.end_time = datetime.now()
        
        self._save(execution)
        logger.info(f"Updated execution {execution_id} status: {status}")
    
    def add_log(self, execution_id: str, level: str, message: str, logger_name: Optional[str] = None):
        """添加日志条目"""
        execution = self.get_execution(execution_id)
        if not execution:
            logger.warning(f"Execution not found: {execution_id}")
            return
        
        log_entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            message=message,
            logger_name=logger_name
        )
        
        execution.logs.append(log_entry)
        self._save(execution)
    
    def set_result(self, execution_id: str, result: Dict[str, Any]):
        """设置执行结果"""
        execution = self.get_execution(execution_id)
        if not execution:
            logger.warning(f"Execution not found: {execution_id}")
            return
        
        execution.result = result
        execution.topic = result.get("topic")
        execution.crew_id = result.get("crew_id")
        execution.agent_ids = result.get("agent_ids", [])
        execution.task_ids = result.get("task_ids", [])
        
        self._save(execution)
        logger.info(f"Set result for execution {execution_id}")
    
    def set_error(self, execution_id: str, error_message: str):
        """设置错误信息"""
        execution = self.get_execution(execution_id)
        if not execution:
            logger.warning(f"Execution not found: {execution_id}")
            return
        
        execution.error_message = error_message
        execution.status = ExecutionStatus.FAILED
        execution.end_time = datetime.now()
        
        self._save(execution)
        logger.info(f"Set error for execution {execution_id}")
    
    def list_executions(self, limit: int = 50) -> List[ExecutionLog]:
        """列出所有执行记录（按时间倒序）"""
        executions = []
        
        for log_file in sorted(self.storage_dir.glob("*.json"), reverse=True):
            try:
                data = json.loads(log_file.read_text(encoding="utf-8"))
                executions.append(ExecutionLog(**data))
                
                if len(executions) >= limit:
                    break
            except Exception as e:
                logger.error(f"Failed to load {log_file}: {e}")
        
        return executions
    
    def _save(self, execution: ExecutionLog):
        """保存执行记录"""
        log_path = self._get_log_path(execution.id)
        
        # 使用 model_dump 替代 dict()
        data = execution.model_dump(mode='json')
        log_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# 全局单例
execution_log_service = ExecutionLogService()
