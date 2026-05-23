"""创作策略 — 注册中心

统一导出策略基类和具体策略，并提供 get_strategy() 工厂函数。
"""

from crewai_web.web.services.creativity.strategy import (
    CreativeStrategy,
    CreativeContext,
    CreativeArtifact,
)
from crewai_web.web.services.creativity.document_strategy import DocumentStrategy
from crewai_web.web.services.creativity.data_analysis_strategy import DataAnalysisStrategy

# ── 策略映射 ──────────────────────────────────────
STRATEGY_MAP: dict[str, CreativeStrategy] = {
    "document": DocumentStrategy(),
    "data-analysis": DataAnalysisStrategy(),
}


def get_strategy(scene_id: str) -> CreativeStrategy:
    """根据场景 ID 获取对应的创作策略"""
    strategy = STRATEGY_MAP.get(scene_id)
    if not strategy:
        raise ValueError(f"场景 '{scene_id}' 暂不支持")
    return strategy


__all__ = [
    "CreativeStrategy",
    "CreativeContext",
    "CreativeArtifact",
    "DocumentStrategy",
    "DataAnalysisStrategy",
    "STRATEGY_MAP",
    "get_strategy",
]
