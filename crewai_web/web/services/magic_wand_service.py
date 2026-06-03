"""魔法棒 — 制品Skill匹配服务

根据场景和用户输入，匹配所需的artifact skills。
优先级: scene_configs预配置 > 本地扫描 > skills.sh远程发现
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from crewai_web.web.config import STORAGE_DIR
from crewai_web.web.services.skills.skill_scanner import SkillScanner
from crewai_web.web.services.skills.skill_metadata_parser import SkillMetadataParser

logger = logging.getLogger(__name__)

# Skill搜索目录
SKILL_SEARCH_DIRS = [
    Path.home() / ".agents" / "skills",
    Path.home() / ".hermes" / "skills",
    Path(__file__).parent.parent.parent.parent / "skills",
]


async def match_artifact_skills(
    scene_id: str,
    user_input: str,
    scene_artifact_skills: List[str] | None = None,
) -> List[Dict[str, Any]]:
    """魔法棒: 匹配制品生成所需的Skills

    Args:
        scene_id: 场景ID
        user_input: 用户输入
        scene_artifact_skills: scene_configs中预配置的artifact_skills

    Returns:
        匹配到的skill列表（按推荐顺序）
    """
    # 优先级1: scene_configs预配置
    if scene_artifact_skills:
        skills = _resolve_skill_names(scene_artifact_skills)
        if skills:
            logger.info(f"[MagicWand] 使用预配置skills: {scene_artifact_skills}")
            return skills

    # 优先级2: 从已安装skills中扫描type=artifact的
    artifact_skills = _scan_installed_artifact_skills()
    if artifact_skills:
        # 用简单关键词匹配
        matched = _keyword_match(user_input, artifact_skills)
        if matched:
            logger.info(f"[MagicWand] 从已安装skills匹配: {[s['name'] for s in matched]}")
            return matched

    # 优先级3: 从installed.json中查找
    installed_artifact_skills = _scan_installed_json_artifact_skills()
    if installed_artifact_skills:
        matched = _keyword_match(user_input, installed_artifact_skills)
        if matched:
            logger.info(f"[MagicWand] 从installed.json匹配: {[s['name'] for s in matched]}")
            return matched

    # 优先级4: 根据场景ID推断
    inferred = _infer_skills_from_scene(scene_id)
    if inferred:
        logger.info(f"[MagicWand] 从场景推断: {[s['name'] for s in inferred]}")
        return inferred

    logger.warning(f"[MagicWand] 未找到匹配的artifact skills: scene={scene_id}")
    return []


def _resolve_skill_names(skill_names: List[str]) -> List[Dict[str, Any]]:
    """解析skill名称列表为详细信息"""
    parser = SkillMetadataParser()
    results = []

    for name in skill_names:
        found = False
        for search_dir in SKILL_SEARCH_DIRS:
            skill_dir = search_dir / name
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                metadata = parser.parse(skill_md)
                results.append({
                    "name": name,
                    "path": str(skill_md),
                    "metadata": metadata,
                    "output_type": metadata.get("output_type", ""),
                })
                found = True
                break

        if not found:
            # 尝试从installed.json加载
            installed = _load_from_installed_json(name)
            if installed:
                results.append(installed)

    return results


def _scan_installed_artifact_skills() -> List[Dict[str, Any]]:
    """扫描已安装的artifact类型skills"""
    parser = SkillMetadataParser()
    results = []

    for search_dir in SKILL_SEARCH_DIRS:
        if not search_dir.exists():
            continue
        for skill_dir in search_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue
            try:
                metadata = parser.parse(skill_md)
                if metadata.get("type") == "artifact":
                    results.append({
                        "name": skill_dir.name,
                        "path": str(skill_md),
                        "metadata": metadata,
                        "output_type": metadata.get("output_type", ""),
                    })
            except Exception:
                continue

    return results


def _scan_installed_json_artifact_skills() -> List[Dict[str, Any]]:
    """从installed.json扫描artifact类型skills"""
    installed_file = STORAGE_DIR / "skills" / "installed.json"
    if not installed_file.exists():
        return []

    try:
        skills = json.loads(installed_file.read_text(encoding="utf-8"))
        results = []
        for s in skills:
            name = s.get("name", "")
            # 根据名称推断是否是artifact类型
            if _is_likely_artifact_skill(name):
                results.append({
                    "name": name,
                    "path": f"installed:{name}",
                    "metadata": {"type": "artifact"},
                    "output_type": _name_to_output_type(name),
                })
        return results
    except Exception:
        return []


def _load_from_installed_json(skill_name: str) -> Optional[Dict[str, Any]]:
    """从installed.json加载单个skill"""
    installed_file = STORAGE_DIR / "skills" / "installed.json"
    if not installed_file.exists():
        return None

    try:
        skills = json.loads(installed_file.read_text(encoding="utf-8"))
        for s in skills:
            if s.get("name") == skill_name:
                return {
                    "name": skill_name,
                    "path": f"installed:{skill_name}",
                    "metadata": {"type": "artifact"},
                    "output_type": _name_to_output_type(skill_name),
                }
    except Exception:
        pass
    return None


def _keyword_match(user_input: str, skills: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """简单关键词匹配"""
    input_lower = user_input.lower()
    matched = []

    # 关键词到skill的映射
    keyword_map = {
        "ppt": ["pptx"],
        "pptx": ["pptx"],
        "演示": ["pptx"],
        "幻灯片": ["pptx"],
        "presentation": ["pptx"],
        "文档": ["documentation-writer"],
        "document": ["documentation-writer"],
        "报告": ["documentation-writer"],
        "report": ["documentation-writer"],
        "excel": ["excel-automation"],
        "表格": ["excel-automation"],
        "数据": ["excel-automation"],
        "sheet": ["excel-automation"],
    }

    # 收集匹配的skill名称
    matched_names = set()
    for keyword, skill_names in keyword_map.items():
        if keyword in input_lower:
            matched_names.update(skill_names)

    # 从skills列表中筛选
    for skill in skills:
        if skill["name"] in matched_names:
            matched.append(skill)

    return matched


def _infer_skills_from_scene(scene_id: str) -> List[Dict[str, Any]]:
    """根据场景ID推断需要的skills"""
    scene_skill_map = {
        "ppt": ["pptx"],
        "document": ["documentation-writer"],
        "data-analysis": ["excel-automation"],
        "excel": ["excel-automation"],
        "code": ["code-generator"],
    }

    skill_names = scene_skill_map.get(scene_id, [])
    return _resolve_skill_names(skill_names)


def _is_likely_artifact_skill(name: str) -> bool:
    """判断skill名称是否可能是artifact类型"""
    artifact_keywords = [
        "pptx", "ppt", "document", "docx", "excel", "xlsx",
        "pdf", "video", "mp4", "music", "mp3", "image",
        "report", "presentation", "documentation",
    ]
    name_lower = name.lower()
    return any(kw in name_lower for kw in artifact_keywords)


def _name_to_output_type(name: str) -> str:
    """从skill名称推断输出类型"""
    name_lower = name.lower()
    if "pptx" in name_lower or "ppt" in name_lower:
        return "pptx"
    if "docx" in name_lower or "document" in name_lower:
        return "docx"
    if "xlsx" in name_lower or "excel" in name_lower:
        return "xlsx"
    if "pdf" in name_lower:
        return "pdf"
    if "video" in name_lower or "mp4" in name_lower:
        return "mp4"
    if "music" in name_lower or "mp3" in name_lower:
        return "mp3"
    return ""
