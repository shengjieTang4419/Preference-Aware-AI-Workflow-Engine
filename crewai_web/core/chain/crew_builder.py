"""
CrewBuilder - 从 ExecutionContext 构建 CrewAI 对象

纯工具类，不包含调度逻辑。
"""

import logging
from typing import Any, Dict, List, Optional

from crewai import Agent, Task

from crewai_web.core.ai.client import AIClient
from crewai_web.core.llm.config_loader import config_loader
from crewai_web.core.tools import get_skills_manager

logger = logging.getLogger(__name__)


class CrewBuilder:
    """Crew 构建工具 - 从配置创建 CrewAI Agent/Task"""

    def build_agent(self, agent_config: Any, inputs: Optional[Dict] = None, model_tier: Optional[str] = None) -> Agent:
        """从配置创建 CrewAI Agent

        Args:
            agent_config: Agent 配置
            inputs: 输入参数（用于替换占位符）
            model_tier: 模型档位 ("basic" | "standard" | "advanced")，None 则使用默认
        """
        # 获取 LLM
        llm = self._get_llm_for_tier(model_tier)

        role = agent_config.role
        goal = agent_config.goal
        backstory = agent_config.backstory

        if inputs:
            for key, value in inputs.items():
                placeholder = "{" + key + "}"
                role = role.replace(placeholder, str(value))
                goal = goal.replace(placeholder, str(value))
                backstory = backstory.replace(placeholder, str(value))

        manager = get_skills_manager()
        skills_config_dict = None
        if agent_config.skills_config:
            skills_config_dict = agent_config.skills_config.model_dump()
        skills = manager.get_skills_for_agent(role, skills_config_dict)

        return Agent(
            role=role,
            goal=goal,
            backstory=backstory,
            allow_delegation=agent_config.allow_delegation,
            verbose=True,
            llm=llm,
            max_execution_time=agent_config.max_execution_time,
            skills=skills,
        )

    def _get_llm_for_tier(self, model_tier: Optional[str] = None):
        """根据模型档位获取 LLM

        Args:
            model_tier: 模型档位 ("basic" | "standard" | "advanced")
                       如果为 None，使用默认配置

        Returns:
            LLM 实例

        Raises:
            ValueError: 如果 model_tier 不为 None 但找不到配置
        """
        if not model_tier:
            logger.info("[CrewBuilder] No model tier specified, using default LLM")
            return AIClient.get_default().llm

        # 获取默认 provider 下该档位的模型配置（找不到会抛异常）
        tier_config = config_loader.get_model_config_by_default_provider(model_tier)
        model_name = tier_config["model"]

        logger.info(f"[CrewBuilder] Using tier '{model_tier}' → model '{model_name}'")

        # AIClient.create() 会自动处理：
        # 1. provider=None → 使用 default_provider
        # 2. temperature 不传 → 通过 resolve_temperature() 从配置读取
        return AIClient.create(model=model_name).llm

    def build_task(
        self,
        task_config: Any,
        agent: Agent,
        context_tasks: List[Task],
        inputs: Optional[Dict] = None,
    ) -> Task:
        """从配置创建 CrewAI Task"""
        description = task_config.description
        expected_output = task_config.expected_output

        if inputs:
            for key, value in inputs.items():
                placeholder = "{" + key + "}"
                description = description.replace(placeholder, str(value))
                expected_output = expected_output.replace(placeholder, str(value))

        return Task(
            description=description,
            expected_output=expected_output,
            agent=agent,
            context=context_tasks if context_tasks else None,
            async_execution=task_config.async_execution,
        )
