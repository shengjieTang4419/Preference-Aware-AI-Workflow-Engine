"""
AI 驱动的 Skills 推荐服务
使用 LLM 智能推荐 Agent 应该使用的 Skills
"""

import logging
from typing import List, Dict, Any
from pydantic import BaseModel, Field

from crewai_web.core.ai import AIClient
from crewai_web.web.services.skills_service import get_skills_service

logger = logging.getLogger(__name__)


class SkillRecommendation(BaseModel):
    """Skills 推荐结果"""

    skill_name: str = Field(..., description="Skill 名称")
    reason: str = Field(..., description="推荐理由")
    priority: str = Field(..., description="优先级: high | medium | low")


class SkillsRecommendationResponse(BaseModel):
    """Skills 推荐响应"""

    recommended_skills: List[SkillRecommendation] = Field(..., description="推荐的 Skills 列表")
    mode: str = Field(default="hybrid", description="推荐的模式: auto | manual | hybrid")


class SkillsRecommender:
    """AI Skills 推荐器"""

    def __init__(self):
        self.ai_client = AIClient.get_default()
        self.skills_service = get_skills_service()

    async def recommend_for_agent(self, role: str, goal: str, backstory: str, task_context: str = "") -> Dict[str, Any]:
        """
        为 Agent 推荐 Skills

        Args:
            role: Agent 角色
            goal: Agent 目标
            backstory: Agent 背景
            task_context: 任务上下文（可选）

        Returns:
            Skills 配置字典
        """
        # 1. 获取所有可用的 Skills
        all_skills = self.skills_service.list_all_skills()

        if not all_skills:
            logger.warning("No skills available for recommendation")
            return {"mode": "auto", "preferred": [], "auto_match": True, "include_patterns": [], "exclude_patterns": []}

        # 2. 构建 Skills 描述
        skills_info = self._format_skills_for_prompt(all_skills)

        # 3. 构建推荐 prompt
        task_context_line = f"- 任务上下文：{task_context}" if task_context else ""
        prompt = self.ai_client.load_prompt(
            "generator/skills_recommendation.prompt",
            role=role,
            goal=goal,
            backstory=backstory,
            task_context_line=task_context_line,
            available_skills=skills_info,
        )

        # 4. 调用 AI 获取推荐
        try:
            recommendation = await self.ai_client.call(
                prompt=prompt, response_model=SkillsRecommendationResponse, role=role
            )

            # 5. 转换为 skills_config 格式
            skills_config = self._convert_to_config(recommendation)

            logger.info(f"AI recommended {len(skills_config['preferred'])} skills for {role}")
            return skills_config

        except Exception as e:
            logger.error(f"Failed to get AI recommendation: {e}")
            # 降级：返回默认配置
            return {"mode": "auto", "preferred": [], "auto_match": True, "include_patterns": [], "exclude_patterns": []}

    def _format_skills_for_prompt(self, skills: List[Dict[str, Any]]) -> str:
        """格式化 Skills 信息用于 prompt"""
        lines = []
        for skill in skills:
            name = skill["name"]
            desc = skill["metadata"].get("description", "No description")
            has_scripts = "✓" if skill["has_scripts"] else "✗"
            lines.append(f"- **{name}** (Tools: {has_scripts}): {desc}")

        return "\n".join(lines)

    def _convert_to_config(self, recommendation: SkillsRecommendationResponse) -> Dict[str, Any]:
        """将推荐结果转换为 skills_config 格式"""
        # 按优先级分组
        high_priority = []
        medium_priority = []

        for skill_rec in recommendation.recommended_skills:
            if skill_rec.priority == "high":
                high_priority.append(skill_rec.skill_name)
            elif skill_rec.priority == "medium":
                medium_priority.append(skill_rec.skill_name)

        # 构建配置
        config = {
            "mode": recommendation.mode,
            "preferred": high_priority + medium_priority,
            "auto_match": recommendation.mode in ["auto", "hybrid"],
            "include_patterns": [],
            "exclude_patterns": [],
        }

        return config

    async def explain_recommendation(self, role: str, recommended_skills: List[str]) -> str:
        """
        解释为什么推荐这些 Skills

        Args:
            role: Agent 角色
            recommended_skills: 推荐的 Skills 列表

        Returns:
            推荐理由说明
        """
        prompt = f"""
请解释为什么为 "{role}" 这个角色推荐以下 Skills：

{', '.join(recommended_skills)}

要求：
1. 简洁明了（2-3 句话）
2. 说明这些 Skills 如何帮助该角色完成任务
3. 使用中文
"""

        try:
            explanation = await self.ai_client.call(prompt=prompt, inject_preferences=False)
            return explanation.strip()
        except Exception as e:
            logger.error(f"Failed to explain recommendation: {e}")
            return "这些 Skills 与该角色的职责相关，能够帮助完成任务。"


# 全局单例
_recommender_instance = None


def get_skills_recommender() -> SkillsRecommender:
    """获取 Skills 推荐器单例"""
    global _recommender_instance
    if _recommender_instance is None:
        _recommender_instance = SkillsRecommender()
    return _recommender_instance
