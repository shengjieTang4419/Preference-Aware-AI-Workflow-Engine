"""
Skill 推荐器
职责：根据角色推荐相关的 skills
"""
from typing import List, Dict, Any


class SkillRecommender:
    """Skill 推荐器"""

    # 角色关键词映射
    ROLE_KEYWORDS = {
        "python": ["python", "code", "generator"],
        "java": ["java", "code", "generator"],
        "javascript": ["javascript", "js", "code", "generator"],
        "typescript": ["typescript", "ts", "code", "generator"],
        "前端": ["frontend", "ui", "web"],
        "后端": ["backend", "api", "server"],
        "测试": ["test", "qa"],
    }

    @staticmethod
    def recommend_for_role(role: str, all_skills: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """根据角色推荐相关的 skills"""
        role_lower = role.lower()

        # 查找匹配的关键词
        relevant_keywords = []
        for keyword, skills_keywords in SkillRecommender.ROLE_KEYWORDS.items():
            if keyword in role_lower:
                relevant_keywords.extend(skills_keywords)

        # 如果没有匹配，返回所有
        if not relevant_keywords:
            return all_skills

        # 过滤相关的 skills
        relevant_skills = []
        for skill in all_skills:
            skill_name_lower = skill["name"].lower()
            skill_desc_lower = skill["metadata"].get("description", "").lower()

            # 检查是否匹配任何关键词
            for keyword in relevant_keywords:
                if keyword in skill_name_lower or keyword in skill_desc_lower:
                    relevant_skills.append(skill)
                    break

        return relevant_skills if relevant_skills else all_skills
