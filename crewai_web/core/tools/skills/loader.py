"""
Skills 加载器
负责将 skill 目录转换为 CrewAI Skill 对象
"""
import logging
from typing import List, Dict
from pathlib import Path

from crewai.skills.models import Skill as SkillModel
from crewai.skills.parser import load_skill_metadata
from crewai.skills.loader import activate_skill

from .scanner import SkillDirectory

logger = logging.getLogger(__name__)


class SkillsLoader:
    """将 skill 目录转换为 CrewAI Skill 对象"""
    
    def __init__(self):
        self._cache: Dict[str, SkillModel] = {}
    
    def load(self, skill_dirs: List[SkillDirectory]) -> List[SkillModel]:
        """
        加载 skill 目录为 CrewAI Skill 对象
        
        Args:
            skill_dirs: skill 目录列表
            
        Returns:
            已激活的 Skill 对象列表
        """
        skills = []
        
        for skill_dir in skill_dirs:
            try:
                skill = self._load_single(skill_dir)
                if skill:
                    skills.append(skill)
            except Exception as e:
                logger.error(f"Failed to load skill {skill_dir.name}: {e}")
        
        logger.info(f"Loaded {len(skills)} skill objects")
        return skills
    
    def _load_single(self, skill_dir: SkillDirectory) -> SkillModel | None:
        """
        加载单个 skill
        
        使用缓存避免重复加载
        """
        cache_key = str(skill_dir.path)
        
        if cache_key in self._cache:
            logger.debug(f"Using cached skill: {skill_dir.name}")
            return self._cache[cache_key]
        
        try:
            skill = load_skill_metadata(skill_dir.path)
            activated = activate_skill(skill)
            
            self._cache[cache_key] = activated
            logger.debug(f"Loaded skill: {skill_dir.name}")
            return activated
            
        except Exception as e:
            logger.error(f"Failed to load skill metadata from {skill_dir.path}: {e}")
            return None
    
    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
