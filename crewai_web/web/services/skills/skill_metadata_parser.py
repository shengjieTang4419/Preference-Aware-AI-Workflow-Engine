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

                    # 简单解析 YAML（支持嵌套 key: value）
                    metadata = SkillMetadataParser._parse_frontmatter(frontmatter)

                    # 提取描述（第一段文字）
                    if not metadata.get("description"):
                        for line in body.split("\n"):
                            line = line.strip()
                            if line and not line.startswith("#"):
                                metadata["description"] = line[:200]
                                break

                    # 标准化新字段
                    metadata.setdefault("type", "tool")  # tool | artifact
                    metadata.setdefault("output_type", "")
                    metadata.setdefault("input_requires", [])
                    metadata.setdefault("execution", {})

                    return metadata

            # 如果没有 frontmatter，从内容提取
            return {
                "name": skill_name,
                "description": "No description available",
                "type": "tool",
                "output_type": "",
                "input_requires": [],
                "execution": {},
            }

        except Exception as e:
            logger.error(f"Failed to parse skill metadata from {skill_md_path}: {e}")
            return {"name": skill_md_path.parent.name, "description": "Error loading skill"}

    @staticmethod
    def _parse_frontmatter(frontmatter: str) -> Dict[str, Any]:
        """解析 YAML frontmatter，支持列表和嵌套"""
        metadata = {}
        current_key = None
        current_list = None

        for line in frontmatter.split("\n"):
            stripped = line.strip()
            if not stripped:
                continue

            # 列表项
            if stripped.startswith("- "):
                if current_key and current_list is not None:
                    current_list.append(stripped[2:].strip().strip('"'))
                continue

            # key: value
            if ":" in stripped:
                key, value = stripped.split(":", 1)
                key = key.strip()
                value = value.strip().strip('"')

                # 判断是否是列表的开始（值为空）
                if not value:
                    current_key = key
                    current_list = []
                    metadata[key] = current_list
                else:
                    current_key = key
                    current_list = None
                    # 尝试解析JSON值
                    if value.startswith("[") or value.startswith("{"):
                        try:
                            import json
                            metadata[key] = json.loads(value)
                        except Exception:
                            metadata[key] = value
                    else:
                        metadata[key] = value

        return metadata

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
