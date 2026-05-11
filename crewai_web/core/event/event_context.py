"""
EventContext - 步骤间共享状态（强类型 dataclass）
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict


@dataclass
class EventContext:
    """Pipeline 上下文 - 在各步骤间传递数据"""

    # 输入（初始化时确定）
    execution_id: str
    scenario: str
    doc_filenames: Optional[List[str]] = None

    # 中间产物（各步骤写入）
    topic: Optional[str] = None
    tasks_plan: Optional[List[dict]] = None
    agents_mapping: Optional[Dict[str, str]] = None
    crew_id: Optional[str] = None
    task_ids: Optional[List[str]] = None
    agent_model_assignments: Optional[Dict[str, str]] = None

    # 最终结果
    success: bool = False
    error: Optional[str] = None

    def to_result(self) -> dict:
        """转换为 API 返回结果"""
        return {
            "topic": self.topic,
            "crew_id": self.crew_id,
            "agent_ids": list(self.agents_mapping.values()) if self.agents_mapping else [],
            "task_ids": self.task_ids or [],
            "agent_model_assignments": self.agent_model_assignments or {},
            "summary": f"已创建 Crew：{self.topic}，包含 {len(self.agents_mapping or {})} 个 Agents 和 {len(self.task_ids or [])} 个 Tasks",
        }
