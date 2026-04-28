"""
执行输出文件管理器
职责：管理执行结果的输出文件（output_dir 下的文件）
"""
from pathlib import Path
from typing import List, Dict, Optional


def get_output_files(exec_id: str) -> List[Dict]:
    """获取输出文件树"""
    from crewai_web.web.services.execution_service import get_execution as _get_exec
    execution = _get_exec(exec_id)
    if not execution:
        return []

    output_dir = Path(execution.output_dir)
    if not output_dir.exists():
        return []

    results = []
    for item in output_dir.rglob("*"):
        if item.name.startswith("."):
            continue

        rel_path = item.relative_to(output_dir)

        if item.is_dir():
            results.append({
                "name": item.name,
                "path": str(rel_path),
                "is_dir": True,
            })
        else:
            full_path = output_dir / rel_path
            f = item.name
            results.append({
                "name": f,
                "path": str(rel_path),
                "size": full_path.stat().st_size,
                "is_dir": False,
            })

    return results


def get_output_file_path(exec_id: str, file_path: str) -> Optional[Path]:
    """获取输出文件的完整路径，不存在返回 None"""
    from crewai_web.web.services.execution_service import get_execution as _get_exec
    execution = _get_exec(exec_id)
    if not execution:
        return None

    output_dir = Path(execution.output_dir)
    target = output_dir / file_path

    try:
        target.resolve().relative_to(output_dir.resolve())
    except ValueError:
        return None

    if not target.exists() or not target.is_file():
        return None

    return target


def read_output_file(exec_id: str, file_path: str) -> Optional[str]:
    """读取输出文件内容"""
    from crewai_web.web.services.execution_service import get_execution as _get_exec
    execution = _get_exec(exec_id)
    if not execution:
        return None

    output_dir = Path(execution.output_dir)
    target = output_dir / file_path

    # 安全检查：确保在 output_dir 内
    try:
        target.resolve().relative_to(output_dir.resolve())
    except ValueError:
        return None  # 路径逃逸

    if not target.exists() or target.is_dir():
        return None

    with open(target, "r", encoding="utf-8") as f:
        return f.read()
