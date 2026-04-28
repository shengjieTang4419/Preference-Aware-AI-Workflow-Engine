"""
Skill 扫描器
职责：扫描 skills 目录，构建 skill 列表
"""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from .skill_metadata_parser import SkillMetadataParser

logger = logging.getLogger(__name__)


class SkillScanner:
    """Skill 扫描器"""

    def __init__(self, search_directories: List[Path]):
        self.search_directories = search_directories
        self.parser = SkillMetadataParser()

    def scan_all(self) -> List[Dict[str, Any]]:
        """扫描所有 skills 目录"""
        skills_list = []

        for skills_dir in self.search_directories:
            if not skills_dir.exists():
                continue

            logger.info(f"Scanning skills directory: {skills_dir}")

            for skill_dir in skills_dir.iterdir():
                if not skill_dir.is_dir():
                    continue

                skill_md = skill_dir / "SKILL.md"
                if not skill_md.exists():
                    continue

                try:
                    skill_info = self._build_skill_info(skill_dir, skill_md)
                    skills_list.append(skill_info)
                except Exception as e:
                    logger.error(f"Failed to load skill {skill_dir.name}: {e}")

        logger.info(f"Found {len(skills_list)} skills")
        return skills_list

    def get_skill_detail(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """获取单个 skill 的详细信息"""
        for skills_dir in self.search_directories:
            skill_dir = skills_dir / skill_name
            skill_md = skill_dir / "SKILL.md"

            if skill_md.exists():
                try:
                    skill_info = self._build_skill_info(skill_dir, skill_md)
                    # 添加完整内容
                    skill_info["content"] = skill_md.read_text(encoding="utf-8")
                    # 添加脚本列表
                    skill_info["scripts"] = self.parser.get_scripts_info(skill_dir)
                    return skill_info
                except Exception as e:
                    logger.error(f"Failed to get skill detail for {skill_name}: {e}")
                    return None

        return None

    def _build_skill_info(self, skill_dir: Path, skill_md: Path) -> Dict[str, Any]:
        """构建 skill 信息字典"""
        metadata = self.parser.parse(skill_md)
        return {
            "name": skill_dir.name,
            "path": str(skill_md),
            "metadata": metadata,
            "has_scripts": self.parser.has_scripts(skill_dir)
        }
