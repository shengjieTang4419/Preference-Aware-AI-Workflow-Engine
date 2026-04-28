"""
执行上下文收集器
职责：从执行记录中收集生成提案所需的上下文信息
"""
from pathlib import Path
from typing import Optional, Dict, List, Any


class ExecutionContextCollector:
    """执行上下文收集器"""

    @staticmethod
    def collect_from_execution(exec_id: str) -> Optional[Dict[str, Any]]:
        """从执行记录收集上下文"""
        from crewai_web.web.services import execution_service, agent_service, task_service, crew_service

        execution = execution_service.get_execution(exec_id)
        if not execution:
            return None

        crew = crew_service.get_crew(execution.crew_id)
        if not crew:
            return None

        agents_config = [
            agent.model_dump()
            for agent_id in crew.agent_ids
            if (agent := agent_service.get_agent(agent_id))
        ]

        tasks_config = [
            task.model_dump()
            for task_id in crew.task_ids
            if (task := task_service.get_task(task_id))
        ]

        result_text = ExecutionContextCollector._read_execution_result(execution.output_dir)

        return {
            "exec_id": exec_id,
            "exec_topic": crew.name,
            "requirement": execution.requirement,
            "crew_config": crew.model_dump(),
            "agents_config": agents_config,
            "tasks_config": tasks_config,
            "execution_result": result_text,
            "user_interventions": [],
        }

    @staticmethod
    def _read_execution_result(output_dir: str) -> str:
        """读取执行结果文本"""
        try:
            output_path = Path(output_dir)
            for fname in ("result.txt", "README.md"):
                candidate = output_path / fname
                if candidate.exists():
                    return candidate.read_text(encoding="utf-8")
        except Exception:
            pass
        return ""
