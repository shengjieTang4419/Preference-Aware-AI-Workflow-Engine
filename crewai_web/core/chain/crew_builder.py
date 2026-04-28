"""
CrewBuilder - 从 ExecutionContext 构建 CrewAI 对象

纯工具类，不包含调度逻辑。
"""

from typing import Any, Dict, List, Optional

from crewai import Agent, Task

from crewai_web.core.llm import LLMFactory
from crewai_web.core.tools import get_skills_manager


class CrewBuilder:
    """Crew 构建工具 - 从配置创建 CrewAI Agent/Task"""

    def __init__(self):
        self.llm_factory = LLMFactory()

    def build_agent(self, agent_config: Any, inputs: Optional[Dict] = None) -> Agent:
        """从配置创建 CrewAI Agent"""
        llm = self.llm_factory.get_llm(agent_config.llm_key or "default")

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
