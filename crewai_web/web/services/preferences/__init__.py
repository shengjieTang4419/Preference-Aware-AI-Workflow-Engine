"""
偏好进化子模块（已重构）
"""
from .models import SuggestedPreference, PreferenceEvolutionProposal
from .proposal_prompt_builder import ProposalPromptBuilder
from .proposal_storage import ProposalStorage
from .proposal_diff_generator import ProposalDiffGenerator
from .execution_context_collector import ExecutionContextCollector
from .proposal_generator import ProposalGenerator
from .proposal_query_service import ProposalQueryService
from .proposal_merge_service import ProposalMergeService

__all__ = [
    "SuggestedPreference",
    "PreferenceEvolutionProposal",
    "ProposalPromptBuilder",
    "ProposalStorage",
    "ProposalDiffGenerator",
    "ExecutionContextCollector",
    "ProposalGenerator",
    "ProposalQueryService",
    "ProposalMergeService",
]
