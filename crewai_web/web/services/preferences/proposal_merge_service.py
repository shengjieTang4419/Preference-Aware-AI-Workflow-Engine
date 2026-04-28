"""
提案合并服务 - 负责合并和拒绝提案
"""
import logging
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime

from crewai_web.web.services.preferences_loader import get_preferences
from crewai_web.web.services.preferences import PreferenceEvolutionProposal

logger = logging.getLogger(__name__)


class ProposalMergeService:
    """提案合并服务 - 处理提案的合并和拒绝"""
    
    def merge(self, proposal: PreferenceEvolutionProposal) -> bool:
        """合并提案到 preferences.md"""
        try:
            preferences_loader = get_preferences()
            pref_file = preferences_loader.preferences_file
            
            # 备份原文件
            backup_path = pref_file.parent / f"preferences.md.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            if pref_file.exists():
                shutil.copy(pref_file, backup_path)
                logger.info(f"Backed up preferences.md to {backup_path}")
            
            # 写入新内容
            pref_file.write_text(proposal.suggested_content, encoding="utf-8")
            
            # 清除缓存
            preferences_loader._cache = None
            
            logger.info(f"Successfully merged proposal {proposal.exec_id} into preferences.md")
            return True
        except Exception as e:
            logger.error(f"Failed to merge proposal {proposal.exec_id}: {e}")
            return False
    
    def reject(self, exec_id: str, reason: Optional[str] = None) -> bool:
        """拒绝提案（标记为已拒绝，但不删除）"""
        # 可以在这里添加拒绝标记到存储，暂时简单处理为日志记录
        logger.info(f"Proposal {exec_id} rejected. Reason: {reason}")
        return True
