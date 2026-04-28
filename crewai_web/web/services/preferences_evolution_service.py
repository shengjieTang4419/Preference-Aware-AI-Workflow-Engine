"""
偏好进化服务 - 编排层
职责：协调各个子模块完成偏好进化流程
"""
import logging
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field

from crewai_web.core.ai import AIClient
from crewai_web.web.services.preferences_loader import get_preferences
from crewai_web.web.services.preferences import (
    SuggestedPreference,
    PreferenceEvolutionProposal,
    ProposalPromptBuilder,
    ProposalStorage,
    ProposalDiffGenerator,
    ExecutionContextCollector,
)

logger = logging.getLogger(__name__)


class PreferencesEvolutionService:
    """偏好进化服务 - 编排层"""
    
    def __init__(self):
        self.ai_client = AIClient()
        self.storage = ProposalStorage()
        self.prompt_builder = ProposalPromptBuilder()
        self.diff_generator = ProposalDiffGenerator()
        self.context_collector = ExecutionContextCollector()
    
    async def generate_proposal(
        self,
        exec_id: str,
        exec_topic: str,
        requirement: str,
        crew_config: Dict[str, Any],
        agents_config: List[Dict[str, Any]],
        tasks_config: List[Dict[str, Any]],
        execution_result: str,
        user_interventions: Optional[List[str]] = None
    ) -> PreferenceEvolutionProposal:
        """基于本次执行生成偏好进化提案"""
        # 1. 获取当前偏好
        original_content = get_preferences().load_preferences_only()
        
        # 2. 构建 Prompt
        prompt = self.prompt_builder.build_evolution_prompt(
            original_content=original_content,
            requirement=requirement,
            crew_config=crew_config,
            agents_config=agents_config,
            tasks_config=tasks_config,
            execution_result=execution_result,
            user_interventions=user_interventions or [],
            exec_id=exec_id,
        )
        
        # 3. 调用 LLM 生成建议
        try:
            suggested_content = await self.ai_client.call(prompt, inject_preferences=False)
            suggested_content = self.prompt_builder.clean_llm_output(suggested_content)
        except Exception as e:
            logger.error(f"Failed to generate preference evolution: {e}")
            suggested_content = original_content
        
        # 4. 生成 diff 摘要
        diff_summary = await self._generate_diff_summary(original_content, suggested_content)
        
        # 5. 解析结构化建议
        suggestions = self.diff_generator.parse_suggestions(suggested_content, exec_id)
        
        # 6. 创建并保存提案
        proposal = PreferenceEvolutionProposal(
            exec_id=exec_id,
            exec_topic=exec_topic,
            original_content=original_content,
            suggested_content=suggested_content,
            diff_summary=diff_summary,
            suggestions=suggestions,
            created_at=datetime.now().isoformat()
        )
        
        self.storage.save(proposal)
        logger.info(f"Generated preference evolution proposal for exec {exec_id}")
        return proposal
    
    async def _generate_diff_summary(self, original: str, suggested: str) -> str:
        """生成人类可读的 diff 摘要"""
        prompt = self.prompt_builder.build_diff_summary_prompt(original, suggested)
        try:
            summary = await self.ai_client.call(prompt, inject_preferences=False)
            return summary.strip()
        except Exception:
            return "生成摘要失败，请手动对比查看"
    
    def get_proposal(self, exec_id: str) -> Optional[PreferenceEvolutionProposal]:
        """获取指定执行的提案"""
        return self.storage.get(exec_id)
    
    def list_proposals(self, limit: int = 20) -> List[PreferenceEvolutionProposal]:
        """列出所有提案（按时间倒序）"""
        return self.storage.list_all(limit)
    
    def merge_proposal(self, exec_id: str) -> bool:
        """合并提案到 preferences.md"""
        proposal = self.get_proposal(exec_id)
        if not proposal:
            logger.error(f"Proposal {exec_id} not found")
            return False
        
        try:
            preferences_loader = get_preferences()
            pref_file = preferences_loader.preferences_file
            
            # 备份原文件
            backup_path = pref_file.parent / f"preferences.md.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            if pref_file.exists():
                shutil.copy(pref_file, backup_path)
            
            # 写入新内容
            pref_file.write_text(proposal.suggested_content, encoding="utf-8")
            preferences_loader._cache = None
            
            logger.info(f"Successfully merged proposal {exec_id} into preferences.md")
            return True
        except Exception as e:
            logger.error(f"Failed to merge proposal {exec_id}: {e}")
            return False
    
    def reject_proposal(self, exec_id: str, reason: Optional[str] = None) -> bool:
        """拒绝提案（标记为已拒绝，但不删除）"""
        proposal = self.get_proposal(exec_id)
        if not proposal:
            return False
        
        # 可以在这里添加拒绝标记，暂时简单处理为不操作
        logger.info(f"Proposal {exec_id} rejected. Reason: {reason}")
        return True

    def list_proposals_summary(self, limit: int = 20) -> List[dict]:
        """获取提案摘要列表（供 Controller 直接返回）"""
        proposals = self.list_proposals(limit)
        return [
            {
                "exec_id": p.exec_id,
                "exec_topic": p.exec_topic,
                "created_at": p.created_at,
                "diff_summary": p.diff_summary[:100] + "..." if len(p.diff_summary) > 100 else p.diff_summary,
                "suggestions_count": len(p.suggestions),
                "status": "pending",
            }
            for p in proposals
        ]

    def get_proposal_detail(self, exec_id: str) -> Optional[dict]:
        """获取提案详情（供 Controller 直接返回）"""
        proposal = self.get_proposal(exec_id)
        if not proposal:
            return None
        return {
            "exec_id": proposal.exec_id,
            "exec_topic": proposal.exec_topic,
            "original_content": proposal.original_content,
            "suggested_content": proposal.suggested_content,
            "diff_summary": proposal.diff_summary,
            "suggestions": [s.model_dump() for s in proposal.suggestions],
            "created_at": proposal.created_at,
        }

    def get_proposal_diff(self, exec_id: str) -> Optional[dict]:
        """获取提案的行级 diff 视图"""
        proposal = self.get_proposal(exec_id)
        if not proposal:
            return None
        lines, stats = self.diff_generator.generate_line_diff(proposal.original_content, proposal.suggested_content)
        return {"exec_id": exec_id, "lines": lines, "stats": stats}

    async def evolve_from_execution(self, exec_id: str) -> Optional[dict]:
        """基于某次执行生成偏好进化提案"""
        context = self.context_collector.collect_from_execution(exec_id)
        if not context:
            return None

        proposal = await self.generate_proposal(**context)

        return {
            "status": "generated",
            "exec_id": exec_id,
            "diff_summary": proposal.diff_summary,
            "suggestions_count": len(proposal.suggestions),
            "view_url": f"/api/preferences/proposals/{exec_id}",
        }


# 全局单例
_preferences_evolution_service: Optional[PreferencesEvolutionService] = None


def get_preferences_evolution_service() -> PreferencesEvolutionService:
    """获取偏好进化服务单例"""
    global _preferences_evolution_service
    if _preferences_evolution_service is None:
        _preferences_evolution_service = PreferencesEvolutionService()
    return _preferences_evolution_service
