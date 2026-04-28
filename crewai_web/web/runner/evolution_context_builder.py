"""
偏好进化上下文构建器
"""
from typing import Dict, Any
from crewai_web.web.runner.dynamic_crew_builder import DynamicCrewBuilder


class EvolutionContextBuilder:
    """偏好进化上下文构建器"""

    @staticmethod
    def build_context(
        exec_id: str,
        requirement: str,
        builder: DynamicCrewBuilder,
        result_text: str,
    ) -> Dict[str, Any]:
        """构建偏好进化所需的上下文"""
        crew_config = {
            "id": builder.crew_config.id,
            "name": builder.crew_config.name,
            "process_type": builder.crew_config.process_type,
            "agent_ids": builder.crew_config.agent_ids,
            "task_ids": builder.crew_config.task_ids,
        }

        agents_config = [
            {
                "id": a.id,
                "role": a.role,
                "goal": a.goal,
                "backstory": a.backstory,
                "llm_key": a.llm_key,
                "skills_config": a.skills_config.model_dump() if a.skills_config else None,
            }
            for a in builder.agent_configs.values()
        ]

        tasks_config = [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "expected_output": t.expected_output,
                "agent_id": t.agent_id,
                "async_execution": t.async_execution,
            }
            for t in builder.task_configs.values()
        ]

        return {
            "exec_id": exec_id,
            "exec_topic": builder.crew_config.name,
            "requirement": requirement,
            "crew_config": crew_config,
            "agents_config": agents_config,
            "tasks_config": tasks_config,
            "execution_result": result_text,
            "user_interventions": [],
        }
