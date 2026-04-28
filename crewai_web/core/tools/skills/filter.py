"""
Skills 过滤器
根据配置过滤 skills
"""
import logging
import fnmatch
from typing import List, Dict, Any

from .scanner import SkillDirectory

logger = logging.getLogger(__name__)


class SkillsFilter:
    """根据配置过滤 skills"""
    
    @staticmethod
    def filter(
        skill_dirs: List[SkillDirectory],
        config: Dict[str, Any] | None = None
    ) -> List[SkillDirectory]:
        """
        根据配置过滤 skill 目录
        
        Args:
            skill_dirs: 所有 skill 目录
            config: 过滤配置，支持：
                - mode: 'auto' | 'manual'
                - preferred: List[str] - 优先使用的 skill 名称
                - auto_match: bool - 是否自动匹配
                - include_patterns: List[str] - 包含模式（支持通配符）
                - exclude_patterns: List[str] - 排除模式（支持通配符）
                
        Returns:
            过滤后的 skill 目录列表
        """
        if not config:
            return skill_dirs
        
        mode = config.get("mode", "auto")
        preferred = config.get("preferred", [])
        auto_match = config.get("auto_match", True)
        include_patterns = config.get("include_patterns", [])
        exclude_patterns = config.get("exclude_patterns", [])
        
        result = []
        
        # 1. 添加优先 skills
        if preferred:
            for skill_dir in skill_dirs:
                if skill_dir.name in preferred:
                    result.append(skill_dir)
                    logger.debug(f"Preferred skill: {skill_dir.name}")
        
        # 2. 如果是 manual 模式，只返回优先的
        if mode == "manual":
            logger.info(f"Manual mode: selected {len(result)} preferred skills")
            return result
        
        # 3. auto 模式：应用模式匹配
        if auto_match:
            for skill_dir in skill_dirs:
                # 跳过已添加的
                if skill_dir in result:
                    continue
                
                # 检查排除模式
                if SkillsFilter._match_patterns(skill_dir.name, exclude_patterns):
                    logger.debug(f"Excluded skill: {skill_dir.name}")
                    continue
                
                # 检查包含模式（如果指定了 include_patterns）
                if include_patterns:
                    if not SkillsFilter._match_patterns(skill_dir.name, include_patterns):
                        logger.debug(f"Not included skill: {skill_dir.name}")
                        continue
                
                result.append(skill_dir)
        
        logger.info(f"Filtered {len(result)} skills from {len(skill_dirs)}")
        return result
    
    @staticmethod
    def _match_patterns(name: str, patterns: List[str]) -> bool:
        """检查名称是否匹配任一模式（支持通配符）"""
        return any(fnmatch.fnmatch(name, pattern) for pattern in patterns)
