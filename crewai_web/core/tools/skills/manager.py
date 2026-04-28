"""
Skills 管理器
统一的门面，整合 Scanner、Loader、Filter
"""
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from crewai.skills.models import Skill as SkillModel

from .config import SkillsConfig
from .scanner import SkillsScanner, SkillDirectory
from .loader import SkillsLoader
from .filter import SkillsFilter

logger = logging.getLogger(__name__)


class SkillsManager:
    """Skills 统一管理器"""
    
    def __init__(self, search_dirs: Optional[List[Path]] = None):
        """
        Args:
            search_dirs: 要扫描的目录列表，默认从配置读取
        """
        if search_dirs is None:
            search_dirs = SkillsConfig.get_skills_directories()
        
        self.scanner = SkillsScanner(search_dirs)
        self.loader = SkillsLoader()
        self.filter = SkillsFilter()
        
        logger.info(f"SkillsManager initialized with {len(search_dirs)} directories")
    
    def get_all_skills(self, force_refresh: bool = False) -> List[SkillModel]:
        """
        获取所有可用的 skills
        
        Args:
            force_refresh: 是否强制刷新缓存
            
        Returns:
            所有 Skill 对象列表
        """
        skill_dirs = self.scanner.scan(force_refresh=force_refresh)
        return self.loader.load(skill_dirs)
    
    def get_skills_for_agent(
        self,
        agent_role: str,
        config: Optional[Dict[str, Any]] = None
    ) -> List[SkillModel]:
        """
        根据 Agent 角色和配置获取相关的 skills
        
        Args:
            agent_role: Agent 角色（当前未使用，预留用于智能推荐）
            config: 过滤配置
            
        Returns:
            过滤后的 Skill 对象列表
        """
        # 1. 扫描所有 skill 目录
        all_skill_dirs = self.scanner.scan()
        
        # 2. 应用过滤
        filtered_dirs = self.filter.filter(all_skill_dirs, config)
        
        # 3. 加载为 Skill 对象
        skills = self.loader.load(filtered_dirs)
        
        logger.info(f"Selected {len(skills)} skills for agent '{agent_role}'")
        return skills
    
    def get_skill_by_name(self, name: str) -> Optional[SkillModel]:
        """
        根据名称获取单个 skill
        
        Args:
            name: skill 名称
            
        Returns:
            Skill 对象，如果不存在返回 None
        """
        skill_dir = self.scanner.get_by_name(name)
        if not skill_dir:
            return None
        
        skills = self.loader.load([skill_dir])
        return skills[0] if skills else None
    
    def get_all_skill_directories(self) -> List[SkillDirectory]:
        """
        获取所有 skill 目录信息（不加载为对象）
        
        用于 UI 展示、统计等场景
        
        Returns:
            SkillDirectory 列表
        """
        return self.scanner.scan()
    
    def refresh(self):
        """刷新所有缓存"""
        self.scanner.invalidate_cache()
        self.loader.clear_cache()
        logger.info("Skills cache refreshed")
    
    @property
    def search_directories(self) -> List[Path]:
        """获取搜索目录列表"""
        return self.scanner.search_dirs


# 全局单例
_manager_instance: Optional[SkillsManager] = None


def get_skills_manager() -> SkillsManager:
    """获取全局 SkillsManager 实例"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = SkillsManager()
    return _manager_instance
