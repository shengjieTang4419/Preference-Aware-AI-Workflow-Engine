"""Prompt 模板加载器"""

import re
from pathlib import Path


class PromptLoader:
    """Prompt 模板加载器"""
    
    def __init__(self, prompts_dir: Path | str):
        """
        初始化 Prompt Loader
        
        Args:
            prompts_dir: Prompt 模板目录
        """
        self.prompts_dir = Path(prompts_dir)
    
    def load(self, template_path: str, **kwargs) -> str:
        """
        从文件加载 Prompt 模板并填充变量
        
        Args:
            template_path: 模板文件路径（相对于 prompts_dir）
            **kwargs: 模板变量
        
        Returns:
            填充后的 Prompt
            
        Raises:
            FileNotFoundError: 模板文件不存在
        
        Example:
            loader = PromptLoader("./prompts")
            prompt = loader.load(
                "generator/topic.txt",
                scenario="开发 AI 平台",
                context_section="上下文：教育领域"
            )
        """
        template_file = self.prompts_dir / template_path
        
        if not template_file.exists():
            raise FileNotFoundError(f"Prompt template not found: {template_file}")
        
        template = template_file.read_text(encoding="utf-8")
        
        result = template
        for key, value in kwargs.items():
            replacement = str(value)
            result = re.sub(r'\{' + re.escape(key) + r'\}', lambda _: replacement, result)
        return result
