"""通知消息模板"""

from typing import Optional


# 成功通知模板
SUCCESS_NOTIFICATION_TEMPLATE = """✅ Crew 执行完成

Crew: {crew_name}
Execution: {exec_id}
Duration: {duration}
Result: {result_preview}"""


# 失败通知模板
FAILURE_NOTIFICATION_TEMPLATE = """❌ Crew 执行失败

Crew: {crew_name}
Execution: {exec_id}
Error: {error}"""


def generate_success_notification(
    crew_name: str,
    exec_id: str,
    duration: Optional[float],
    result: Optional[str],
    preview_length: int = 200,
) -> str:
    """生成成功通知消息
    
    Args:
        crew_name: Crew 名称
        exec_id: 执行 ID
        duration: 执行时长（秒）
        result: 执行结果
        preview_length: 结果预览长度
        
    Returns:
        通知消息内容
    """
    result_preview = result[:preview_length] if result else "N/A"
    if result and len(result) > preview_length:
        result_preview += "..."
    
    return SUCCESS_NOTIFICATION_TEMPLATE.format(
        crew_name=crew_name,
        exec_id=exec_id,
        duration=f"{duration:.2f}s" if duration else "N/A",
        result_preview=result_preview,
    )


def generate_failure_notification(
    crew_name: str,
    exec_id: str,
    error: Optional[str],
) -> str:
    """生成失败通知消息
    
    Args:
        crew_name: Crew 名称
        exec_id: 执行 ID
        error: 错误信息
        
    Returns:
        通知消息内容
    """
    return FAILURE_NOTIFICATION_TEMPLATE.format(
        crew_name=crew_name,
        exec_id=exec_id,
        error=error or "Unknown error",
    )
