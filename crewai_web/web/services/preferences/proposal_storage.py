"""
偏好进化提案存储管理器
职责：提案的持久化、读取、列表
"""
import json
import logging
from pathlib import Path
from typing import Optional, List
from .models import PreferenceEvolutionProposal

logger = logging.getLogger(__name__)


class ProposalStorage:
    """提案存储管理器"""

    def __init__(self, storage_dir: Optional[Path] = None):
        if storage_dir is None:
            storage_dir = Path(__file__).parent.parent.parent.parent.parent / "storage" / "preference_proposals"
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save(self, proposal: PreferenceEvolutionProposal) -> None:
        """保存提案"""
        proposal_path = self.storage_dir / f"{proposal.exec_id}.json"
        with open(proposal_path, "w", encoding="utf-8") as f:
            json.dump(proposal.model_dump(), f, ensure_ascii=False, indent=2)

    def get(self, exec_id: str) -> Optional[PreferenceEvolutionProposal]:
        """获取指定执行的提案"""
        proposal_path = self.storage_dir / f"{exec_id}.json"

        if not proposal_path.exists():
            return None

        try:
            with open(proposal_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return PreferenceEvolutionProposal(**data)
        except Exception as e:
            logger.error(f"Failed to load proposal {exec_id}: {e}")
            return None

    def list_all(self, limit: int = 20) -> List[PreferenceEvolutionProposal]:
        """列出所有提案（按时间倒序）"""
        proposals = []

        for proposal_file in sorted(self.storage_dir.glob("*.json"), reverse=True):
            try:
                with open(proposal_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                proposals.append(PreferenceEvolutionProposal(**data))
                if len(proposals) >= limit:
                    break
            except Exception as e:
                logger.error(f"Failed to load proposal {proposal_file}: {e}")

        return proposals
