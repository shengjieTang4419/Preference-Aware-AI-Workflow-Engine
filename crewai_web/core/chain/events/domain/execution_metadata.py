"""执行元数据 Domain 对象"""

from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any


@dataclass
class ExecutionMetadata:
    """执行元数据 - Domain 对象
    
    表示一次 Crew 执行的元数据，包含执行 ID、状态、指标等信息。
    """

    execution_id: str
    requirement: str
    crew_id: str
    process_type: str
    success: bool
    completed_at: str
    duration_seconds: Optional[float] = None
    input_folder: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None

    def to_dict(self) -> dict:
        """转换为字典，用于 JSON 序列化
        
        Returns:
            可 JSON 序列化的字典
        """
        data = asdict(self)
        
        # 确保 metrics 可 JSON 化
        if data.get("metrics"):
            data["metrics"] = self._serialize_metrics(data["metrics"])
        
        return data
    
    @staticmethod
    def _serialize_metrics(metrics: dict) -> dict:
        """序列化 metrics，确保可 JSON 化
        
        Args:
            metrics: 原始 metrics 字典
            
        Returns:
            可 JSON 序列化的 metrics 字典
        """
        return {
            k: str(v) if not isinstance(v, (int, float, bool, type(None))) else v
            for k, v in metrics.items()
        }
