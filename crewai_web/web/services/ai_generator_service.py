"""
AI 生成服务 - 编排层
协调 TaskGenerator 和 AgentGenerator 完成 Crew 生成
"""

import logging
from typing import Dict, Optional
from crewai_web.core.ai import AIClient
from crewai_web.web.services.task_generator import task_generator
from crewai_web.web.services.agent_generator import agent_generator
from crewai_web.web.services import crew_service
from crewai_web.web.domain.crew import CrewCreate

logger = logging.getLogger(__name__)


class AIGeneratorService:
    """AI 驱动的 Crew 配置生成器（编排层）"""

    def __init__(self):
        self.ai_client = AIClient.get_default()

    async def generate_crew_from_scenario(
        self, scenario: str, user_context: Optional[str] = None, execution_id: Optional[str] = None
    ) -> Dict:
        """
        从场景描述生成完整的 Crew 配置

        Args:
            scenario: 用户输入的问题/场景描述
            user_context: 额外的上下文信息

        Returns:
            {
                "topic": str,
                "crew_id": str,
                "agent_ids": List[str],
                "task_ids": List[str],
                "summary": str
            }
        """
        logger.info(f"[Crew Generation] Starting for scenario: {scenario[:100]}...")

        # 1. 生成 Topic
        topic = await self._generate_topic(scenario, user_context)
        logger.info(f"[Crew Generation] Topic: {topic}")

        # 2. 生成 Tasks 规划
        tasks_plan = await task_generator.generate_tasks_plan(scenario, topic, user_context)
        logger.info(f"[Crew Generation] Tasks planned: {len(tasks_plan)}")

        # 3. 匹配/创建 Agents
        agents_mapping = await agent_generator.match_or_create_agents(tasks_plan)
        logger.info(f"[Crew Generation] Agents ready: {len(agents_mapping)}")

        # 4. 创建 Crew（先创建，获取 crew_id）
        crew_id = self._create_crew(topic, list(agents_mapping.values()), [])
        logger.info(f"[Crew Generation] Crew created: {crew_id}")

        # 5. 创建 Tasks（传入完整的上下文信息）
        task_ids = task_generator.create_tasks(
            tasks_plan, agents_mapping, topic=topic, crew_id=crew_id, execution_id=execution_id
        )
        logger.info(f"[Crew Generation] Tasks created: {len(task_ids)}")

        # 6. AI 模型分配
        from crewai_web.web.services.model_assignment_service import model_assignment_service

        agent_model_assignments = await model_assignment_service.assign_models_for_crew(
            crew_name=topic, process_type="sequential", agent_ids=list(agents_mapping.values()), task_ids=task_ids
        )
        logger.info(f"[Crew Generation] Model assignments completed: {agent_model_assignments}")

        # 7. 更新 Crew（task_ids + agent_model_assignments）
        from crewai_web.web.services import crew_service
        from crewai_web.web.domain.crew import CrewUpdate

        crew_service.update_crew(
            crew_id, CrewUpdate(task_ids=task_ids, agent_model_assignments=agent_model_assignments)
        )
        logger.info(f"[Crew Generation] Crew updated with task_ids and model assignments")

        return {
            "topic": topic,
            "crew_id": crew_id,
            "agent_ids": list(agents_mapping.values()),
            "task_ids": task_ids,
            "agent_model_assignments": agent_model_assignments,
            "summary": f"已创建 Crew：{topic}，包含 {len(agents_mapping)} 个 Agents 和 {len(task_ids)} 个 Tasks",
        }

    async def _generate_topic(self, scenario: str, context: Optional[str] = None) -> str:
        """生成项目主题"""
        context_section = f"上下文：{context}" if context else ""

        prompt = self.ai_client.load_prompt(
            "generator/topic.prompt", scenario=scenario, context_section=context_section
        )

        topic = await self.ai_client.call(prompt, role="TopicGenerator")
        return topic.strip()

    def _create_crew(self, topic: str, agent_ids: list[str], task_ids: list[str]) -> str:
        """创建 Crew"""
        crew_data = CrewCreate(
            name=topic,
            description=f"AI 自动生成的 Crew：{topic}",
            agent_ids=agent_ids,
            task_ids=task_ids,
            process_type="sequential",
        )

        created_crew = crew_service.create_crew(crew_data)
        return created_crew.id


# 全局单例
ai_generator_service = AIGeneratorService()
