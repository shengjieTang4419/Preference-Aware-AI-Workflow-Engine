"""
偏好进化服务 - 编排层（已重构）
职责：协调各个子服务完成偏好进化流程

重构说明：
- ProposalGenerator: 提案生成核心逻辑
- ProposalQueryService: 查询和视图转换
- ProposalMergeService: 合并和拒绝操作
"""
import logging
from typing import Optional, Dict, Any, List

from crewai_web.web.services.preferences import (
    PreferenceEvolutionProposal,
    ProposalStorage,
    ExecutionContextCollector,
)
from crewai_web.web.services.preferences.proposal_generator import ProposalGenerator
from crewai_web.web.services.preferences.proposal_query_service import ProposalQueryService
from crewai_web.web.services.preferences.proposal_merge_service import ProposalMergeService

logger = logging.getLogger(__name__)


class PreferencesEvolutionService:
    """偏好进化服务 - 编排层（已重构为更小的子服务）"""
    
    def __init__(self):
        self.generator = ProposalGenerator()
        self.query_service = ProposalQueryService()
        self.merge_service = ProposalMergeService()
        self.storage = ProposalStorage()
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
        """基于本次执行生成偏好进化提案（委托给 ProposalGenerator）"""
        proposal = await self.generator.generate(
            exec_id=exec_id,
            exec_topic=exec_topic,
            requirement=requirement,
            crew_config=crew_config,
            agents_config=agents_config,
            tasks_config=tasks_config,
            execution_result=execution_result,
            user_interventions=user_interventions
        )
        
        # 保存提案
        self.storage.save(proposal)
        return proposal
    
    def get_proposal(self, exec_id: str) -> Optional[PreferenceEvolutionProposal]:
        """获取指定执行的提案（委托给 QueryService）"""
        return self.query_service.get(exec_id)
    
    def list_proposals(self, limit: int = 20) -> List[PreferenceEvolutionProposal]:
        """列出所有提案（委托给 QueryService）"""
        return self.query_service.list_all(limit)
    
    def merge_proposal(self, exec_id: str) -> bool:
        """合并提案到 preferences.md（委托给 MergeService）"""
        proposal = self.get_proposal(exec_id)
        if not proposal:
            logger.error(f"Proposal {exec_id} not found")
            return False
        return self.merge_service.merge(proposal)
    
    def reject_proposal(self, exec_id: str, reason: Optional[str] = None) -> bool:
        """拒绝提案（委托给 MergeService）"""
        return self.merge_service.reject(exec_id, reason)

    def list_proposals_summary(self, limit: int = 20) -> List[dict]:
        """获取提案摘要列表（委托给 QueryService）"""
        return self.query_service.get_summary_list(limit)

    def get_proposal_detail(self, exec_id: str) -> Optional[dict]:
        """获取提案详情（委托给 QueryService）"""
        return self.query_service.get_detail(exec_id)

    def get_proposal_diff(self, exec_id: str) -> Optional[dict]:
        """获取提案的行级 diff 视图（委托给 QueryService）"""
        return self.query_service.get_diff(exec_id)

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
