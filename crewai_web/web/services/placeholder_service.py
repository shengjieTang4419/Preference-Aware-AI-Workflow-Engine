"""
占位符提取服务
从 Crew 配置中提取所有占位符
"""
import re
from typing import Set, List
from crewai_web.web.services import agent_service, task_service, crew_service


def extract_placeholders(text: str) -> Set[str]:
    """
    从文本中提取所有占位符
    例如: "为 {product_idea} 设计 {feature}" -> {"product_idea", "feature"}
    """
    if not text:
        return set()
    
    # 匹配 {xxx} 格式的占位符
    pattern = r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}'
    matches = re.findall(pattern, text)
    return set(matches)


def get_crew_placeholders(crew_id: str) -> List[str]:
    """
    获取 Crew 中所有的占位符
    
    Returns:
        去重后的占位符列表，按字母顺序排序
    """
    crew = crew_service.get_crew(crew_id)
    if not crew:
        raise ValueError(f"Crew '{crew_id}' not found")
    
    all_placeholders: Set[str] = set()
    
    # 1. 从所有 Agents 中提取占位符
    for agent_id in crew.agent_ids:
        agent = agent_service.get_agent(agent_id)
        if agent:
            all_placeholders.update(extract_placeholders(agent.role))
            all_placeholders.update(extract_placeholders(agent.goal))
            all_placeholders.update(extract_placeholders(agent.backstory))
    
    # 2. 从所有 Tasks 中提取占位符
    for task_id in crew.task_ids:
        task = task_service.get_task(task_id)
        if task:
            all_placeholders.update(extract_placeholders(task.name))
            all_placeholders.update(extract_placeholders(task.description))
            all_placeholders.update(extract_placeholders(task.expected_output))
    
    # 3. 从 Crew 描述中提取占位符
    if crew.description:
        all_placeholders.update(extract_placeholders(crew.description))
    
    # 返回排序后的列表
    return sorted(list(all_placeholders))
