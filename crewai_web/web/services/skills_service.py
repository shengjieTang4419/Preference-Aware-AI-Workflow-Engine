"""
Skills 服务 - 编排层
职责：协调各个子模块完成 skills 管理
"""
import logging
from typing import List, Dict, Any, Optional

from crewai_web.core.tools import get_skills_manager
from crewai_web.web.services.skills import (
    SkillScanner,
    SkillRecommender,
    SkillStatistics,
)

logger = logging.getLogger(__name__)


class SkillsService:
    """Skills 管理服务 - 编排层"""
    
    def __init__(self):
        self.manager = get_skills_manager()
        self.scanner = SkillScanner(self.manager.search_directories)
        self.recommender = SkillRecommender()
        self.statistics = SkillStatistics()
    
    def list_all_skills(self) -> List[Dict[str, Any]]:
        """获取所有可用的 Skills"""
        return self.scanner.scan_all()
    
    def get_skill_detail(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """获取单个 Skill 的详细信息"""
        return self.scanner.get_skill_detail(skill_name)
    
    def get_skills_for_role(self, role: str) -> List[Dict[str, Any]]:
        """根据角色推荐相关的 Skills"""
        all_skills = self.list_all_skills()
        return self.recommender.recommend_for_role(role, all_skills)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取 Skills 统计信息"""
        all_skills = self.list_all_skills()
        return self.statistics.generate(all_skills)


# 全局单例
_skills_service_instance: Optional[SkillsService] = None


def get_skills_service() -> SkillsService:
    """获取 Skills 服务单例"""
    global _skills_service_instance
    if _skills_service_instance is None:
        _skills_service_instance = SkillsService()
    return _skills_service_instance
