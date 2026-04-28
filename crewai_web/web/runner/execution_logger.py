"""
执行日志捕获器
"""
from typing import List, Callable


class ExecutionLogger:
    """执行日志捕获器"""

    def __init__(self, exec_id: str, log_callback: Callable[[str, str], None]):
        self.exec_id = exec_id
        self.log_callback = log_callback
        self.logs: List[str] = []

    def log(self, level: str, msg: str):
        """记录日志"""
        log_line = f"[{level}] {msg}"
        self.logs.append(log_line)
        self.log_callback(level, msg)

    def info(self, msg: str):
        self.log("INFO", msg)

    def error(self, msg: str):
        self.log("ERROR", msg)

    def get_all_logs(self) -> str:
        return "\n".join(self.logs)
