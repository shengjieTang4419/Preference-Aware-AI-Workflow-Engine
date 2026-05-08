"""
执行日志工具 - 简单的日志持久化
"""

from crewai_web.web.services.chat_execution_log_service import execution_log_service


class ExecutionLogger:
    """执行日志工具 - 尽可能简单"""

    @staticmethod
    def log(execution_id: str, level: str, message: str, source: str = "crew.generation"):
        """写入一条日志"""
        execution_log_service.add_log(execution_id, level, message, source)


# 全局单例
execution_logger = ExecutionLogger()
