"""
Skills 扫描器
负责扫描文件系统，发现所有有效的 skill 目录
"""
import logging
from pathlib import Path
from typing import List, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SkillDirectory:
    """Skill 目录信息"""
    path: Path
    name: str
    skill_md_path: Path
    source: str  # 'internal' or 'external'
    
    def __hash__(self):
        return hash(self.path)
    
    def __eq__(self, other):
        if not isinstance(other, SkillDirectory):
            return False
        return self.path == other.path


class SkillsScanner:
    """扫描并发现 skill 目录"""
    
    def __init__(self, search_dirs: List[Path]):
        """
        Args:
            search_dirs: 要扫描的根目录列表
        """
        self.search_dirs = search_dirs
        self._cache: Set[SkillDirectory] = set()
        self._cache_valid = False
    
    def scan(self, force_refresh: bool = False) -> List[SkillDirectory]:
        """
        扫描所有 skill 目录
        
        Args:
            force_refresh: 是否强制刷新缓存
            
        Returns:
            有效的 skill 目录列表
        """
        if self._cache_valid and not force_refresh:
            return list(self._cache)
        
        self._cache.clear()
        
        for search_dir in self.search_dirs:
            if not search_dir.exists():
                logger.warning(f"Skills directory does not exist: {search_dir}")
                continue
            
            logger.info(f"Scanning skills directory: {search_dir}")
            source = self._determine_source(search_dir)
            
            for item in search_dir.iterdir():
                if not item.is_dir():
                    continue
                
                skill_md = item / "SKILL.md"
                if not skill_md.exists():
                    continue
                
                skill_dir = SkillDirectory(
                    path=item,
                    name=item.name,
                    skill_md_path=skill_md,
                    source=source
                )
                self._cache.add(skill_dir)
                logger.debug(f"Found skill: {skill_dir.name} ({source})")
        
        self._cache_valid = True
        logger.info(f"Scanned {len(self._cache)} skills")
        return list(self._cache)
    
    def _determine_source(self, search_dir: Path) -> str:
        """判断 skill 来源"""
        if "external_skills" in str(search_dir):
            return "external"
        return "internal"
    
    def get_by_name(self, name: str) -> SkillDirectory | None:
        """根据名称获取 skill 目录"""
        if not self._cache_valid:
            self.scan()
        
        for skill_dir in self._cache:
            if skill_dir.name == name:
                return skill_dir
        return None
    
    def invalidate_cache(self):
        """使缓存失效"""
        self._cache_valid = False
