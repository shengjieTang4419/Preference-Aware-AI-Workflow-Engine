"""
Agent 生成器 - 负责 Agent 匹配和创建
"""

import logging
from typing import List, Optional

from crewai_web.core.ai import AIClient
from crewai_web.web.services import agent_service
from crewai_web.web.domain.agent import AgentCreate, SkillsConfig
from crewai_web.web.domain.ai_schemas import AgentConfig, AgentMatchResult, TaskPlan
from crewai_web.web.services.skills_recommender import get_skills_recommender

logger = logging.getLogger(__name__)


class AgentGenerator:
    """Agent 生成器"""

    def __init__(self):
        self.ai_client = AIClient.get_default()

    async def match_or_create_agents(self, tasks_plan: List[TaskPlan]) -> dict[str, str]:
        """
        匹配现有 Agent 或创建新 Agent

        Args:
            tasks_plan: 任务规划列表

        Returns:
            角色类型 -> agent_id 映射
        """
        agents_mapping = {}
        existing_agents = agent_service.list_agents()

        for task in tasks_plan:
            role_type = task.role_type

            if role_type in agents_mapping:
                continue

            # 尝试匹配现有 Agent（使用 AI 语义匹配）
            matched_agent = await self._find_similar_agent(role_type, task.name, existing_agents)

            if matched_agent:
                logger.info(f"Matched existing agent '{matched_agent.role}' for role '{role_type}'")
                agents_mapping[role_type] = matched_agent.id
            else:
                # 创建新 Agent
                logger.info(f"Creating new agent for role '{role_type}'")
                new_agent_id = await self.create_agent(role_type, task.name)
                agents_mapping[role_type] = new_agent_id

        return agents_mapping

    async def _find_similar_agent(self, role_type: str, task_context: str, existing_agents: List) -> Optional[any]:
        """
        使用 AI 查找相似的现有 Agent（语义匹配）

        Args:
            role_type: 角色类型
            task_context: 任务上下文
            existing_agents: 现有 Agent 列表

        Returns:
            匹配的 Agent 或 None
        """
        if not existing_agents:
            return None

        # 构建 Agents 列表字符串
        agents_list = "\n".join(
            [f"- ID: {agent.id}, Role: {agent.role}, Goal: {agent.goal}" for agent in existing_agents]
        )

        # 调用 AI 进行语义匹配
        prompt = self.ai_client.load_prompt(
            "generator/agent_match.prompt", role_type=role_type, task_context=task_context, agents_list=agents_list
        )

        match_result = await self.ai_client.call(prompt=prompt, response_model=AgentMatchResult)

        if match_result.matched and match_result.agent_id:
            # 查找匹配的 Agent 对象
            matched_agent = next((agent for agent in existing_agents if agent.id == match_result.agent_id), None)
            if matched_agent:
                logger.info(f"AI matched agent: {match_result.reason}")
                return matched_agent
            else:
                logger.warning(f"AI returned invalid agent_id: {match_result.agent_id}")
        else:
            logger.info(f"No match found: {match_result.reason}")

        return None

    async def create_agent(self, role_type: str, task_context: str) -> str:
        """
        创建新的 Agent

        Args:
            role_type: 角色类型
            task_context: 任务上下文

        Returns:
            创建的 agent_id
        """
        prompt = self.ai_client.load_prompt("generator/agent.prompt", role_type=role_type, task_context=task_context)

        # 使用 Pydantic 校验（传入 role_type 以获取相关偏好）
        agent_config = await self.ai_client.call(
            prompt=prompt, response_model=AgentConfig, role=role_type  # 传入角色类型，自动注入相关偏好
        )

        # 使用 role 作为 name（标识符）
        agent_name = agent_config.role.replace(" ", "_").lower()

        # AI 推荐 Skills（可选，失败不影响 Agent 创建）
        skills_config = None
        try:
            logger.info(f"Requesting AI to recommend skills for {agent_config.role}")
            skills_recommender = get_skills_recommender()
            skills_config_dict = await skills_recommender.recommend_for_agent(
                role=agent_config.role,
                goal=agent_config.goal,
                backstory=agent_config.backstory,
                task_context=task_context,
            )

            # 转换为 SkillsConfig 对象
            if skills_config_dict and skills_config_dict.get("preferred"):
                skills_config = SkillsConfig(**skills_config_dict)
                logger.info(
                    f"✅ AI recommended {len(skills_config_dict['preferred'])} skills: {skills_config_dict['preferred']}"
                )
            else:
                logger.info(f"ℹ️  No skills recommended for {agent_config.role} (this is normal)")
        except Exception as e:
            logger.warning(f"⚠️  Skills recommendation failed for {agent_config.role}: {e}")
            logger.info(f"ℹ️  Agent will be created without skills (this is normal)")

        agent_data = AgentCreate(
            name=agent_name,
            role=agent_config.role,
            goal=agent_config.goal,
            backstory=agent_config.backstory,
            allow_delegation=False,
            llm_key="default",
            max_execution_time=600,
            skills_config=skills_config,  # 添加 AI 推荐的 Skills 配置
        )

        created_agent = agent_service.create_agent(agent_data)
        logger.info(f"Created agent '{agent_config.role}' -> {created_agent.id}")

        return created_agent.id


# 全局单例
agent_generator = AgentGenerator()
