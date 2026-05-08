"""
AI 生成服务 - 已重构为 Pipeline 模式

原有编排逻辑已拆分到:
- crewai_web/web/events/ (各步骤事件)
- crewai_web/web/services/crew_generation_pipeline.py (Pipeline 编排)

此文件保留向后兼容的入口，内部委托给 Pipeline。
"""

import logging
from typing import Dict, Optional
from crewai_web.web.services.crew_generation_pipeline import crew_generation_pipeline

logger = logging.getLogger(__name__)


class AIGeneratorService:
    """AI 生成服务 - 委托给 CrewGenerationPipeline"""

    async def generate_crew_from_scenario(self, scenario: str, execution_id: Optional[str] = None) -> Dict:
        """从场景描述生成完整的 Crew 配置"""
        return await crew_generation_pipeline.execute(
            execution_id=execution_id,
            scenario=scenario,
        )


# 全局单例
ai_generator_service = AIGeneratorService()
