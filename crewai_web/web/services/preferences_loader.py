"""
偏好加载服务

根据 .crew/DESIGN.md 设计：
- Agent 执行时：加载 system_rules.md + preferences.md
- 进化服务时：只读取 preferences.md

职责：
1. 加载文件内容
2. 提供缓存机制
3. 不包含进化、提案等业务逻辑（这些应该在 API 层）
"""
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class PreferencesLoader:
    
    def __init__(self, project_root: Optional[Path] = None):
        if project_root is None:
            current = Path(__file__).parent
            while current != current.parent:
                if (current / ".crew").exists() or (current / "pyproject.toml").exists():
                    project_root = current
                    break
                current = current.parent
            else:
                project_root = Path.cwd()
        
        self.project_root = project_root
        self.system_rules_file = project_root / ".crew" / "system_rules.md"
        self.preferences_file = project_root / ".crew" / "preferences.md"
        self._cache: Optional[str] = None
        
        logger.info(f"Preferences loader: {self.system_rules_file}, {self.preferences_file}")
    
    def load(self, force_reload: bool = False) -> str:
        """
        Agent 执行时调用：加载系统规则 + 个人偏好
        
        Returns:
            完整的 system prompt 内容
        """
        if self._cache is not None and not force_reload:
            return self._cache
        
        parts = []
        
        if self.system_rules_file.exists():
            try:
                system_rules = self.system_rules_file.read_text(encoding="utf-8")
                parts.append(system_rules)
                logger.info(f"Loaded system rules: {len(system_rules)} chars")
            except Exception as e:
                logger.error(f"Failed to load system rules: {e}")
        else:
            logger.warning(f"System rules not found: {self.system_rules_file}")
        
        if self.preferences_file.exists():
            try:
                preferences = self.preferences_file.read_text(encoding="utf-8")
                parts.append(preferences)
                logger.info(f"Loaded preferences: {len(preferences)} chars")
            except Exception as e:
                logger.error(f"Failed to load preferences: {e}")
        else:
            logger.warning(f"Preferences not found: {self.preferences_file}")
        
        self._cache = "\n\n".join(parts)
        return self._cache
    
    def load_preferences_only(self) -> str:
        """
        进化服务调用：只加载个人偏好（不包含系统规则）
        
        Returns:
            preferences.md 的内容
        """
        if not self.preferences_file.exists():
            logger.warning(f"Preferences file not found: {self.preferences_file}")
            return ""
        
        try:
            return self.preferences_file.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to load preferences: {e}")
            return ""
    
    def save_preferences(self, content: str) -> None:
        """
        保存偏好内容到 preferences.md
        
        Args:
            content: 新的偏好内容
        """
        try:
            self.preferences_file.parent.mkdir(parents=True, exist_ok=True)
            self.preferences_file.write_text(content, encoding="utf-8")
            self._cache = None
            logger.info(f"Saved preferences: {len(content)} chars")
        except Exception as e:
            logger.error(f"Failed to save preferences: {e}")
            raise
    
    def get_file_path(self) -> Path:
        """获取 preferences.md 文件路径"""
        return self.preferences_file


_preferences_loader: Optional[PreferencesLoader] = None


def get_preferences() -> PreferencesLoader:
    """获取全局偏好加载器实例"""
    global _preferences_loader
    if _preferences_loader is None:
        _preferences_loader = PreferencesLoader()
    return _preferences_loader
