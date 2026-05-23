"""创作策略 — 结构化文档

根据用户输入，调用 LLM 生成专业的 Markdown 文档。
"""

import logging
import uuid
from datetime import datetime
from pathlib import Path

from crewai_web.web.config import ARTIFACTS_DIR
from crewai_web.web.services.llm_service import call_llm
from crewai_web.web.services.creativity.strategy import (
    CreativeStrategy,
    CreativeContext,
    CreativeArtifact,
)

logger = logging.getLogger(__name__)


class DocumentStrategy(CreativeStrategy):
    """结构化文档策略

    流程:
    1. 将用户输入发送给 LLM，请求生成结构化 Markdown 文档
    2. 将 LLM 返回的内容保存为 .md 文件
    3. 返回 CreativeArtifact
    """

    # ── 提示词模板 ──────────────────────────────────

    def get_prompt_template(self) -> str:
        return (
            "你是一位专业的文档撰写专家。请根据用户的输入，生成一份结构清晰、"
            "内容详实的专业 Markdown 文档。\n\n"
            "要求：\n"
            "1. 使用 Markdown 格式，包含标题、子标题、列表、表格等元素\n"
            "2. 内容要有逻辑性，层次分明\n"
            "3. 语言专业但易读\n"
            "4. 如果用户没有指定主题，请根据输入推断最合适的文档类型\n"
            "5. 文档开头请给出一个简洁的标题（使用 # 标记）\n\n"
            "请直接输出 Markdown 内容，不要添加额外的解释。"
        )

    # ── 执行策略 ────────────────────────────────────

    async def execute(self, context: CreativeContext) -> CreativeArtifact:
        """执行文档创作"""
        execution_id = uuid.uuid4().hex[:12]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = ARTIFACTS_DIR / f"{timestamp}_{execution_id}"
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"[文档策略] 开始创作: scene={context.scene_id}, execution={execution_id}")

        # 如果有上传文件，读取其内容附加到 prompt
        file_contents = self._read_input_files(context.input_files)

        # 构建完整 prompt
        system_prompt = self.get_prompt_template()
        user_prompt = context.user_input
        if file_contents:
            user_prompt += "\n\n---\n以下是用户上传的参考文件内容：\n\n" + file_contents

        # 调用 LLM
        logger.info("[文档策略] 调用 LLM 生成文档...")
        try:
            markdown_content = await call_llm(prompt=user_prompt, system_prompt=system_prompt)
        except Exception as e:
            logger.error(f"[文档策略] LLM 调用失败: {e}")
            raise RuntimeError(f"文档生成失败: {e}") from e

        # 提取标题
        title = self._extract_title(markdown_content, context.user_input)

        # 保存为 .md 文件
        file_path = output_dir / f"{title[:50].replace(' ', '_')}.md"
        file_path.write_text(markdown_content, encoding="utf-8")
        logger.info(f"[文档策略] 文件已保存: {file_path}")

        # 生成预览文本（取前 500 字符）
        preview_text = markdown_content[:500]
        if len(markdown_content) > 500:
            preview_text += "\n\n..."

        return CreativeArtifact(
            title=title,
            description=f"基于「{context.user_input[:50]}」生成的结构化文档",
            files=[file_path],
            output_type="markdown",
            preview_text=preview_text,
        )

    # ── 内部方法 ────────────────────────────────────

    def _read_input_files(self, file_paths: list[str]) -> str:
        """读取上传文件内容"""
        if not file_paths:
            return ""

        contents = []
        for fp in file_paths:
            path = Path(fp)
            if not path.exists():
                logger.warning(f"[文档策略] 文件不存在: {fp}")
                continue
            try:
                text = path.read_text(encoding="utf-8")
                contents.append(f"### 文件: {path.name}\n\n{text}")
            except Exception as e:
                logger.warning(f"[文档策略] 读取文件失败 {fp}: {e}")
        return "\n\n".join(contents)

    def _extract_title(self, markdown: str, fallback: str) -> str:
        """从 Markdown 内容中提取标题"""
        for line in markdown.split("\n"):
            line = line.strip()
            if line.startswith("# "):
                return line.lstrip("# ").strip()
        # 回退：取用户输入的前 30 字符
        return fallback[:30].strip() or "未命名文档"
