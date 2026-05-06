"""
模型分配服务 - 使用 AI 为 Agent 分配最优模型等级
"""

import logging
from typing import Dict, List
from crewai_web.core.ai import AIClient
from crewai_web.web.domain.ai_schemas import ModelAssignmentResponse, TaskPlan
from crewai_web.web.services import agent_service, task_service

logger = logging.getLogger(__name__)


class ModelAssignmentService:
    """模型分配服务"""

    def __init__(self):
        self.ai_client = AIClient.get_default()

    async def assign_models_for_crew(
        self, crew_name: str, process_type: str, agent_ids: List[str], task_ids: List[str]
    ) -> Dict[str, str]:
        """
        为 Crew 中的所有 Agent 分配模型等级

        Args:
            crew_name: Crew 名称
            process_type: 执行流程类型
            agent_ids: Agent ID 列表
            task_ids: Task ID 列表

        Returns:
            agent_id -> model_tier 的映射
        """
        logger.info(f"[ModelAssignment] Assigning models for crew '{crew_name}'")

        # 1. 加载 Agent 和 Task 配置
        agents_info = self._build_agents_info(agent_ids)
        tasks_info = self._build_tasks_info(task_ids)

        # 2. 调用 AI 进行模型分配
        prompt = self.ai_client.load_prompt(
            "generator/model_assignment.prompt",
            crew_name=crew_name,
            process_type=process_type,
            agents_info=agents_info,
            tasks_info=tasks_info,
        )

        response = await self.ai_client.call(
            prompt=prompt, response_model=ModelAssignmentResponse, role="ModelAssignmentOptimizer"
        )

        # 3. 转换为 agent_id -> model_tier 映射
        assignments = {}
        for assignment in response.assignments:
            assignments[assignment.agent_id] = assignment.assigned_model_tier
            logger.info(
                f"[ModelAssignment] {assignment.agent_role} -> {assignment.assigned_model_tier} "
                f"(reason: {assignment.reason})"
            )

        logger.info(f"[ModelAssignment] Summary: {response.summary.optimization_note}")
        logger.info(
            f"[ModelAssignment] Distribution: "
            f"basic={response.summary.basic_count}, "
            f"standard={response.summary.standard_count}, "
            f"advanced={response.summary.advanced_count}"
        )

        return assignments

    def _build_agents_info(self, agent_ids: List[str]) -> str:
        """构建 Agents 信息字符串"""
        agents = []
        for agent_id in agent_ids:
            agent = agent_service.get_agent(agent_id)
            if agent:
                agents.append(
                    f"- **Agent ID**: {agent.id}\n"
                    f"  **角色**: {agent.role}\n"
                    f"  **目标**: {agent.goal}\n"
                    f"  **背景**: {agent.backstory}"
                )
        return "\n\n".join(agents) if agents else "无 Agent 信息"

    def _build_tasks_info(self, task_ids: List[str]) -> str:
        """构建 Tasks 信息字符串"""
        tasks = []
        for task_id in task_ids:
            task = task_service.get_task(task_id)
            if task:
                tasks.append(
                    f"- **Task ID**: {task.id}\n"
                    f"  **名称**: {task.name}\n"
                    f"  **描述**: {task.description}\n"
                    f"  **期望输出**: {task.expected_output}\n"
                    f"  **执行 Agent**: {task.agent_id}\n"
                    f"  **角色类型**: {task.role_type or '未指定'}"
                )
        return "\n\n".join(tasks) if tasks else "无 Task 信息"


# 全局单例
model_assignment_service = ModelAssignmentService()
