"""
动态 Crew 构建器
从 storage 中的 JSON 配置动态构建 CrewAI Crew
"""
from crewai import Agent, Task, Crew, Process
from typing import List, Dict, Optional
from pathlib import Path

from crewai_web.web.services import agent_service, task_service, crew_service
from crewai_web.web.domain.agent import AgentOut
from crewai_web.web.domain.task import TaskOut
from crewai_web.web.domain.crew import CrewOut
from crewai_web.core.llm import LLMFactory
from crewai_web.core.tools import get_skills_manager


class DynamicCrewBuilder:
    """动态构建 Crew，从 Web 配置加载而非硬编码"""
    
    def __init__(self, crew_id: str, requirement: str, output_dir: Optional[Path] = None):
        self.crew_id = crew_id
        self.requirement = requirement
        self.output_dir = output_dir
        self.llm_factory = LLMFactory()
        
        # 加载配置
        self.crew_config = crew_service.get_crew(crew_id)
        if not self.crew_config:
            raise ValueError(f"Crew '{crew_id}' not found")
        
        self.agent_configs: Dict[str, AgentOut] = {}
        self.task_configs: Dict[str, TaskOut] = {}
        
        # 加载所有相关的 agents 和 tasks
        for agent_id in self.crew_config.agent_ids:
            agent = agent_service.get_agent(agent_id)
            if not agent:
                raise ValueError(f"Agent '{agent_id}' not found")
            self.agent_configs[agent_id] = agent
        
        for task_id in self.crew_config.task_ids:
            task = task_service.get_task(task_id)
            if not task:
                raise ValueError(f"Task '{task_id}' not found")
            self.task_configs[task_id] = task
    
    def _create_agent(self, agent_config: AgentOut, inputs: Optional[Dict] = None) -> Agent:
        """从配置创建 CrewAI Agent"""
        # 获取 LLM
        llm = self.llm_factory.get_llm(agent_config.llm_key or "default")
        
        # 替换占位符
        role = agent_config.role
        goal = agent_config.goal
        backstory = agent_config.backstory
        
        if inputs:
            for key, value in inputs.items():
                placeholder = "{" + key + "}"
                role = role.replace(placeholder, str(value))
                goal = goal.replace(placeholder, str(value))
                backstory = backstory.replace(placeholder, str(value))
        
        # 加载 Skills
        manager = get_skills_manager()
        
        # 如果 Agent 有 skills_config，使用配置过滤
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
            skills=skills,  # 注入 Skills
        )
    
    def _create_task(
        self, 
        task_config: TaskOut, 
        agent: Agent, 
        context_tasks: List[Task],
        inputs: Optional[Dict] = None
    ) -> Task:
        """从配置创建 CrewAI Task"""
        # 替换占位符（如果有 inputs）
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
    
    def build_crew(self, inputs: Optional[Dict] = None) -> Crew:
        """
        构建 Crew
        
        Args:
            inputs: 占位符替换字典，如 {"product_idea": "AI编程教育平台"}
        """
        # 1. 创建所有 Agents
        agents_map: Dict[str, Agent] = {}
        for agent_id, agent_config in self.agent_configs.items():
            agents_map[agent_id] = self._create_agent(agent_config, inputs)
        
        # 2. 创建所有 Tasks（按顺序，处理依赖关系）
        tasks_map: Dict[str, Task] = {}
        tasks_list: List[Task] = []
        
        for task_id in self.crew_config.task_ids:
            task_config = self.task_configs[task_id]
            
            # 获取该 task 的 agent
            agent = agents_map.get(task_config.agent_id)
            if not agent:
                raise ValueError(f"Agent '{task_config.agent_id}' not found for task '{task_id}'")
            
            # 获取 context tasks（前置依赖任务）
            context_tasks = []
            if task_config.context_task_ids:
                for ctx_task_id in task_config.context_task_ids:
                    ctx_task = tasks_map.get(ctx_task_id)
                    if ctx_task:
                        context_tasks.append(ctx_task)
                    else:
                        # 警告：依赖的任务还未创建（可能是配置错误）
                        print(f"Warning: Context task '{ctx_task_id}' not found for task '{task_id}'")
            
            # 创建 task
            task = self._create_task(task_config, agent, context_tasks, inputs)
            tasks_map[task_id] = task
            tasks_list.append(task)
        
        # 3. 确定执行流程
        process = Process.sequential
        if self.crew_config.process_type == "hierarchical":
            process = Process.hierarchical
        
        # 4. 构建 Crew
        return Crew(
            agents=list(agents_map.values()),
            tasks=tasks_list,
            process=process,
            verbose=True,
            memory=False,
            checkpoint=True,
            output_log_file=str(self.output_dir / "execution.log") if self.output_dir else None,
        )
