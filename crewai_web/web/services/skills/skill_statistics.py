"""
Skill 统计器
职责：生成 skills 统计信息
"""
from pathlib import Path
from typing import List, Dict, Any


class SkillStatistics:
    """Skill 统计器"""

    @staticmethod
    def generate(all_skills: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成统计信息"""
        total_skills = len(all_skills)
        skills_with_scripts = sum(1 for s in all_skills if s["has_scripts"])

        # 按目录分组
        by_directory = {}
        for skill in all_skills:
            skill_path = Path(skill["path"])
            dir_name = skill_path.parent.parent.name
            if dir_name not in by_directory:
                by_directory[dir_name] = 0
            by_directory[dir_name] += 1

        return {
            "total_skills": total_skills,
            "skills_with_scripts": skills_with_scripts,
            "skills_by_directory": by_directory
        }
