"""
Task 生成器 - 负责任务拆解和创建
"""
import logging
from typing import List, Optional
from crewai_web.core.ai import AIClient
from crewai_web.web.services import task_service
from crewai_web.web.domain.ai_schemas import TasksPlanResponse, TaskPlan
from crewai_web.web.domain.task import TaskCreate

logger = logging.getLogger(__name__)


class TaskGenerator:
    """任务生成器"""
    
    def __init__(self):
        self.ai_client = AIClient()
    
    async def generate_tasks_plan(
        self, 
        scenario: str, 
        topic: str, 
        context: Optional[str] = None
    ) -> List[TaskPlan]:
        """
        生成任务规划
        
        Args:
            scenario: 场景描述
            topic: 项目主题
            context: 额外上下文
        
        Returns:
            任务规划列表
        """
        context_section = f"上下文：{context}" if context else ""
        
        prompt = self.ai_client.load_prompt(
            "generator/tasks.prompt",
            topic=topic,
            scenario=scenario,
            context_section=context_section
        )
        
        # 使用 Pydantic 校验
        response = await self.ai_client.call(
            prompt=prompt,
            response_model=TasksPlanResponse
        )
        
        logger.info(f"Generated {len(response.tasks)} tasks")
        return response.tasks
    
    def create_tasks(
        self, 
        tasks_plan: List[TaskPlan], 
        agents_mapping: dict[str, str],
        topic: Optional[str] = None,
        crew_id: Optional[str] = None,
        execution_id: Optional[str] = None
    ) -> List[str]:
        """
        创建 Tasks 记录
        
        Args:
            tasks_plan: 任务规划列表
            agents_mapping: 角色类型 -> agent_id 映射
            topic: 项目主题（新增）
            crew_id: 所属 Crew ID（新增）
            execution_id: 执行 ID（新增）
        
        Returns:
            创建的 task_id 列表
        """
        task_ids = []
        task_id_map = {}  # task_name -> task_id
        
        for task_plan in tasks_plan:
            agent_id = agents_mapping.get(task_plan.role_type)
            
            if not agent_id:
                logger.warning(f"No agent found for role '{task_plan.role_type}', skipping task '{task_plan.name}'")
                continue
            
            # 处理依赖关系
            context_task_ids = []
            for dep_name in task_plan.dependencies:
                if dep_name in task_id_map:
                    context_task_ids.append(task_id_map[dep_name])
                else:
                    logger.warning(f"Dependency '{dep_name}' not found for task '{task_plan.name}'")
            
            task_data = TaskCreate(
                name=task_plan.name,
                description=task_plan.description,
                expected_output=task_plan.expected_output,
                agent_id=agent_id,
                context_task_ids=context_task_ids,
                async_execution=False,
                # 新增：归属信息
                topic=topic,
                crew_id=crew_id,
                execution_id=execution_id,
                role_type=task_plan.role_type
            )
            
            created_task = task_service.create_task(task_data)
            task_ids.append(created_task.id)
            task_id_map[task_plan.name] = created_task.id
            
            logger.info(f"Created task '{task_plan.name}' (topic={topic}, crew={crew_id}) -> {created_task.id}")
        
        return task_ids


# 全局单例
task_generator = TaskGenerator()
