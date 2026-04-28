"""
Skills 配置管理
"""
from pathlib import Path
from typing import List
import os


class SkillsConfig:
    """Skills 目录配置"""
    
    @staticmethod
    def get_skills_directories() -> List[Path]:
        """
        获取 skills 目录列表
        
        目录来源：
        1. /workspace/external_skills - 通过 devcontainer 挂载的外部 skills
           (宿主机路径由环境变量 EXTERNAL_SKILLS_DIR 配置)
        2. 项目内置 skills 目录
        
        Returns:
            存在的 skills 目录列表
        """
        dirs = []
        
        # 1. 外部 skills (devcontainer 挂载)
        external_skills = Path("/workspace/external_skills")
        if external_skills.exists() and any(external_skills.iterdir()):
            # 只有当目录存在且非空时才添加
            dirs.append(external_skills)
        
        # 2. 项目内置 skills
        project_root = Path(__file__).parent.parent.parent.parent.parent
        project_skills = project_root / "skills"
        if project_skills.exists():
            dirs.append(project_skills)
        
        return dirs
