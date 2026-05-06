"""
提案生成器 - 负责生成偏好进化提案的核心逻辑
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from crewai_web.core.ai import AIClient
from crewai_web.web.services.preferences_loader import get_preferences
from crewai_web.web.services.preferences import (
    PreferenceEvolutionProposal,
    ProposalPromptBuilder,
    ProposalDiffGenerator,
)

logger = logging.getLogger(__name__)


class ProposalGenerator:
    """提案生成器 - 核心业务逻辑"""

    def __init__(self):
        self.ai_client = AIClient.get_default()
        self.prompt_builder = ProposalPromptBuilder()
        self.diff_generator = ProposalDiffGenerator()

    async def generate(
        self,
        exec_id: str,
        exec_topic: str,
        requirement: str,
        crew_config: Dict[str, Any],
        agents_config: List[Dict[str, Any]],
        tasks_config: List[Dict[str, Any]],
        execution_result: str,
        user_interventions: Optional[List[str]] = None,
    ) -> PreferenceEvolutionProposal:
        """基于本次执行生成偏好进化提案"""
        # 1. 获取当前偏好
        original_content = get_preferences().load_preferences_only()

        # 2. 构建 Prompt
        prompt = self.prompt_builder.build_evolution_prompt(
            original_content=original_content,
            requirement=requirement,
            crew_config=crew_config,
            agents_config=agents_config,
            tasks_config=tasks_config,
            execution_result=execution_result,
            user_interventions=user_interventions or [],
            exec_id=exec_id,
        )

        # 3. 调用 LLM 生成建议
        try:
            suggested_content = await self.ai_client.call(prompt, inject_preferences=False)
            suggested_content = self.prompt_builder.clean_llm_output(suggested_content)
        except Exception as e:
            logger.error(f"Failed to generate preference evolution: {e}")
            suggested_content = original_content

        # 4. 生成 diff 摘要
        diff_summary = await self._generate_diff_summary(original_content, suggested_content)

        # 5. 解析结构化建议
        suggestions = self.diff_generator.parse_suggestions(suggested_content, exec_id)

        # 6. 创建提案
        proposal = PreferenceEvolutionProposal(
            exec_id=exec_id,
            exec_topic=exec_topic,
            original_content=original_content,
            suggested_content=suggested_content,
            diff_summary=diff_summary,
            suggestions=suggestions,
            created_at=datetime.now().isoformat(),
        )

        logger.info(f"Generated preference evolution proposal for exec {exec_id}")
        return proposal

    async def _generate_diff_summary(self, original: str, suggested: str) -> str:
        """生成人类可读的 diff 摘要"""
        prompt = self.prompt_builder.build_diff_summary_prompt(original, suggested)
        try:
            summary = await self.ai_client.call(prompt, inject_preferences=False)
            return summary.strip()
        except Exception:
            return "生成摘要失败，请手动对比查看"
