"""
提案查询服务 - 负责提案的查询和视图转换
"""
import logging
from typing import Optional, List

from crewai_web.web.services.preferences import (
    PreferenceEvolutionProposal,
    ProposalStorage,
    ProposalDiffGenerator,
)

logger = logging.getLogger(__name__)


class ProposalQueryService:
    """提案查询服务 - 查询和视图转换"""
    
    def __init__(self):
        self.storage = ProposalStorage()
        self.diff_generator = ProposalDiffGenerator()
    
    def get(self, exec_id: str) -> Optional[PreferenceEvolutionProposal]:
        """获取指定执行的提案"""
        return self.storage.get(exec_id)
    
    def list_all(self, limit: int = 20) -> List[PreferenceEvolutionProposal]:
        """列出所有提案（按时间倒序）"""
        return self.storage.list_all(limit)
    
    def get_summary_list(self, limit: int = 20) -> List[dict]:
        """获取提案摘要列表（供 API 返回）"""
        proposals = self.list_all(limit)
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
    
    def get_detail(self, exec_id: str) -> Optional[dict]:
        """获取提案详情（供 API 返回）"""
        proposal = self.get(exec_id)
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
    
    def get_diff(self, exec_id: str) -> Optional[dict]:
        """获取提案的行级 diff 视图"""
        proposal = self.get(exec_id)
        if not proposal:
            return None
        lines, stats = self.diff_generator.generate_line_diff(
            proposal.original_content,
            proposal.suggested_content
        )
        return {
            "exec_id": exec_id,
            "lines": lines,
            "stats": stats
        }
