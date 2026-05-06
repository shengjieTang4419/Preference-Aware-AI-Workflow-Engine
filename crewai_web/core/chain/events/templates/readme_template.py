"""README 模板"""

from typing import Optional


# README 模板
README_TEMPLATE = """# Execution Summary

- **Execution ID**: {exec_id}
- **Requirement**: {requirement}
- **Crew**: {crew_name}
- **Status**: {status}
- **Duration**: {duration}
- **Output Directory**: {output_dir}

## Metrics

- Tasks started: {task_started}
- Tasks completed: {task_completed}
- Tasks failed: {task_failed}

## Result

{result}
"""


def generate_readme(
    exec_id: str,
    requirement: str,
    crew_name: str,
    status: str,
    duration: Optional[float],
    output_dir: str,
    metrics: dict,
    result: Optional[str],
) -> str:
    """生成 README 内容
    
    Args:
        exec_id: 执行 ID
        requirement: 用户需求
        crew_name: Crew 名称
        status: 执行状态（COMPLETED/FAILED）
        duration: 执行时长（秒）
        output_dir: 输出目录
        metrics: 指标字典
        result: 执行结果
        
    Returns:
        README Markdown 内容
    """
    return README_TEMPLATE.format(
        exec_id=exec_id,
        requirement=requirement,
        crew_name=crew_name,
        status=status,
        duration=f"{duration:.2f}s" if duration else "N/A",
        output_dir=output_dir,
        task_started=metrics.get("task_started", 0),
        task_completed=metrics.get("task_completed", 0),
        task_failed=metrics.get("task_failed", 0),
        result=result or "No result",
    )
