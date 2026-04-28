"""
偏好进化 Diff 生成器
职责：生成人类可读的 diff 摘要、行级 diff
"""
import difflib
import re
import logging
from typing import List, Dict
from .models import SuggestedPreference

logger = logging.getLogger(__name__)


class ProposalDiffGenerator:
    """Diff 生成器"""

    @staticmethod
    def generate_line_diff(original: str, suggested: str) -> tuple[List[Dict], Dict]:
        """生成行级 diff"""
        original_lines = original.splitlines(keepends=False)
        suggested_lines = suggested.splitlines(keepends=False)
        diff = difflib.unified_diff(original_lines, suggested_lines, lineterm="")

        lines = []
        line_no = 0
        for i, line in enumerate(diff):
            if i < 2:  # 跳过文件头
                continue
            line_no += 1
            if line.startswith("+"):
                lines.append({"type": "added", "content": line[1:], "line_number": line_no})
            elif line.startswith("-"):
                lines.append({"type": "removed", "content": line[1:], "line_number": line_no})
            else:
                lines.append({"type": "context", "content": line, "line_number": line_no})

        stats = {
            "added": sum(1 for l in lines if l["type"] == "added"),
            "removed": sum(1 for l in lines if l["type"] == "removed"),
            "unchanged": sum(1 for l in lines if l["type"] == "context"),
        }
        return lines, stats

    @staticmethod
    def parse_suggestions(suggested_content: str, exec_id: str) -> List[SuggestedPreference]:
        """解析建议内容为结构化列表（基于注释提取）"""
        suggestions = []

        # 匹配 <!-- 来源: 执行 xxx，置信度: 0.x --> 格式
        pattern = r'(##[^\n]+|###[^\n]+).*?<!--\s*来源:\s*执行\s*([^,]+),\s*置信度:\s*([0-9.]+)\s*-->'
        matches = re.findall(pattern, suggested_content, re.DOTALL)

        for match in matches:
            header, source_exec, confidence = match
            category = header.replace("##", "").replace("###", "").replace("新增:", "").replace("更新:", "").strip()

            suggestions.append(SuggestedPreference(
                category=category,
                content="...",  # 简化处理，前端展示时从完整内容提取
                reason=f"基于执行 {source_exec} 的经验",
                confidence=float(confidence),
                source_exec_id=source_exec
            ))

        return suggestions
