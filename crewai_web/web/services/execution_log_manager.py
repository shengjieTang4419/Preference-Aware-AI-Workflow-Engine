"""
执行日志文件管理器
职责：管理 execution.log 文件的读写
"""
from pathlib import Path
from datetime import datetime
from crewai_web.web.config import EXECUTIONS_DIR


def _exec_dir(exec_id: str) -> Path:
    return EXECUTIONS_DIR / exec_id


def append_log(exec_id: str, level: str, message: str) -> None:
    """追加日志到 execution.log"""
    log_path = _exec_dir(exec_id) / "execution.log"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] [{level}] {message}\n"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line)


def get_logs(exec_id: str) -> str:
    """获取完整日志内容"""
    log_path = _exec_dir(exec_id) / "execution.log"
    if not log_path.exists():
        return ""
    with open(log_path, "r", encoding="utf-8") as f:
        return f.read()
