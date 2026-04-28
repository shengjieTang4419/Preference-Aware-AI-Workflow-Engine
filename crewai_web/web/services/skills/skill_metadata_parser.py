"""
Skill 元数据解析器
职责：解析 SKILL.md 的 frontmatter 和描述
"""
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


class SkillMetadataParser:
    """Skill 元数据解析器"""

    @staticmethod
    def parse(skill_md_path: Path) -> Dict[str, Any]:
        """解析 SKILL.md 的 frontmatter"""
        try:
            content = skill_md_path.read_text(encoding="utf-8")
            skill_name = skill_md_path.parent.name

            # 提取 YAML frontmatter
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = parts[1].strip()
                    body = parts[2].strip()

                    # 简单解析 YAML（只支持基本的 key: value）
                    metadata = {}
                    for line in frontmatter.split("\n"):
                        if ":" in line:
                            key, value = line.split(":", 1)
                            metadata[key.strip()] = value.strip().strip('"')

                    # 提取描述（第一段文字）
                    if not metadata.get("description"):
                        for line in body.split("\n"):
                            line = line.strip()
                            if line and not line.startswith("#"):
                                metadata["description"] = line[:200]
                                break

                    return metadata

            # 如果没有 frontmatter，从内容提取
            return {"name": skill_name, "description": "No description available"}

        except Exception as e:
            logger.error(f"Failed to parse skill metadata from {skill_md_path}: {e}")
            return {"name": skill_md_path.parent.name, "description": "Error loading skill"}

    @staticmethod
    def has_scripts(skill_dir: Path) -> bool:
        """检查是否有可执行脚本"""
        scripts_dir = skill_dir / "scripts"
        if scripts_dir.exists() and scripts_dir.is_dir():
            return len(list(scripts_dir.glob("*.py"))) > 0
        return False

    @staticmethod
    def get_scripts_info(skill_dir: Path) -> list[Dict[str, Any]]:
        """获取脚本列表信息"""
        scripts_dir = skill_dir / "scripts"
        if not scripts_dir.exists():
            return []

        scripts = []
        for script in scripts_dir.glob("*.py"):
            scripts.append({
                "name": script.stem,
                "path": str(script),
                "size": script.stat().st_size
            })
        return scripts
