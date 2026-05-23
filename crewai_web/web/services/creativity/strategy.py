"""创作策略 — 基类与数据结构

定义策略模式的核心接口，所有具体策略均继承 CreativeStrategy。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class CreativeContext:
    """创作上下文"""
    scene_id: str                      # 场景 ID (document/data-analysis/ppt/...)
    user_input: str                    # 用户输入的想法
    input_files: list[str] = field(default_factory=list)  # 上传的文件路径列表
    user_id: Optional[int] = None     # 用户 ID


@dataclass
class CreativeArtifact:
    """创作制品"""
    title: str                         # 制品标题
    description: str                   # 制品说明
    files: list[Path]                  # 生成的文件路径列表
    output_type: str                   # markdown/docx/xlsx/pptx/zip/html/mp3/mp4
    preview_text: str                  # 预览文本（Markdown 格式）


class CreativeStrategy(ABC):
    """创作策略基类"""

    @abstractmethod
    async def execute(self, context: CreativeContext) -> CreativeArtifact:
        """执行创作，返回制品"""
        ...

    @abstractmethod
    def get_prompt_template(self) -> str:
        """获取 LLM 提示词模板"""
        ...
