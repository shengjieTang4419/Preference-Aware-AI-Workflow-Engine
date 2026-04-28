"""
偏好进化 Prompt 构建器
职责：构建 LLM Prompt，清理 LLM 输出
"""
from typing import Dict, List, Any
from pathlib import Path


class ProposalPromptBuilder:
    """偏好进化 Prompt 构建器"""
    
    PROMPTS_DIR = Path(__file__).parent.parent.parent.parent / "prompts" / "preferences"

    @staticmethod
    def _load_prompt_template(filename: str) -> str:
        """加载 prompt 模板文件"""
        prompt_path = ProposalPromptBuilder.PROMPTS_DIR / filename
        return prompt_path.read_text(encoding="utf-8")

    @staticmethod
    def build_evolution_prompt(
        original_content: str,
        requirement: str,
        crew_config: Dict,
        agents_config: List[Dict],
        tasks_config: List[Dict],
        execution_result: str,
        user_interventions: List[str],
        exec_id: str,
    ) -> str:
        """构建进化提示词"""
        agents_info = "\n".join([
            f"- {a.get('role', 'Unknown')}: {a.get('goal', 'No goal')[:100]}..."
            for a in agents_config
        ])

        tasks_info = "\n".join([
            f"- {t.get('name', 'Unknown')}: {t.get('description', 'No desc')[:100]}..."
            for t in tasks_config
        ])

        interventions_info = "\n".join([f"- {i}" for i in user_interventions]) if user_interventions else "无"

        # 加载 prompt 模板
        template = ProposalPromptBuilder._load_prompt_template("evolution.prompt")
        
        # 填充变量
        prompt = template.format(
            original_content=original_content,
            requirement=requirement,
            process_type=crew_config.get('process_type', 'sequential'),
            agents_info=agents_info,
            tasks_info=tasks_info,
            execution_result=execution_result[:2000] + "..." if len(execution_result) > 2000 else execution_result,
            interventions_info=interventions_info,
            exec_id=exec_id
        )
        
        return prompt

    @staticmethod
    def build_diff_summary_prompt(original: str, suggested: str) -> str:
        """构建 diff 摘要 Prompt"""
        # 加载 prompt 模板
        template = ProposalPromptBuilder._load_prompt_template("diff_summary.prompt")
        
        # 填充变量
        prompt = template.format(
            original_length=len(original),
            suggested_length=len(suggested),
            original_content=original,
            suggested_content=suggested
        )
        
        return prompt

    @staticmethod
    def clean_llm_output(content: str) -> str:
        """清理 LLM 输出（移除代码块包裹）"""
        if "```markdown" in content:
            content = content.split("```markdown")[1].split("```")[0].strip()
        elif content.startswith("```"):
            content = content.split("```")[1].split("```")[0].strip()
        return content.strip()
