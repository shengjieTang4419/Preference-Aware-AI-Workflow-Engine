"""创作策略 — 数据分析

上传 CSV/Excel 数据后，调用 LLM 生成分析脚本，
在沙箱子进程中执行，收集图表 (.png) 和分析报告。
"""

import logging
import subprocess
import sys
import tempfile
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

# 子进程执行超时（秒）
SCRIPT_TIMEOUT = 60


class DataAnalysisStrategy(CreativeStrategy):
    """数据分析策略

    流程:
    1. 读取用户上传的 CSV/Excel 数据结构
    2. 发送给 LLM，请求生成 pandas + matplotlib 分析脚本
    3. 在子进程中执行脚本，收集生成的图表和分析文本
    4. 打包为 Markdown 报告 + 图表文件
    5. 返回 CreativeArtifact
    """

    # ── 提示词模板 ──────────────────────────────────

    def get_prompt_template(self) -> str:
        return (
            "你是一位资深的数据分析师和 Python 专家。\n"
            "请根据用户的需求和数据结构，生成一段完整的 Python 分析脚本。\n\n"
            "要求：\n"
            "1. 使用 pandas 读取数据，使用 matplotlib 绘制图表\n"
            "2. 所有图表保存为 PNG 文件到 OUTPUT_DIR 变量指定的目录\n"
            "3. 图表文件名使用英文，如 chart_1.png, chart_2.png\n"
            "4. 在脚本最后，将分析结论以 Markdown 格式写入 OUTPUT_DIR/report.md\n"
            "5. report.md 中引用图表时使用相对路径，如 `![图表](chart_1.png)`\n"
            "6. 中文内容使用中文，图表标签也用中文\n"
            "7. 脚本顶部设置 matplotlib 使用 Agg 后端: matplotlib.use('Agg')\n"
            "8. 设置中文字体: plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']\n"
            "9. 设置负号显示: plt.rcParams['axes.unicode_minus'] = False\n"
            "10. 脚本应包含完整的异常处理\n\n"
            "请只输出 Python 代码，不要添加解释。\n"
            "代码中读取数据的路径使用 DATA_FILE 变量。\n"
            "代码中输出目录使用 OUTPUT_DIR 变量。\n"
            "这两个变量会在执行前由运行环境注入。"
        )

    # ── 执行策略 ────────────────────────────────────

    async def execute(self, context: CreativeContext) -> CreativeArtifact:
        """执行数据分析"""
        execution_id = uuid.uuid4().hex[:12]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = ARTIFACTS_DIR / f"{timestamp}_{execution_id}"
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"[数据分析策略] 开始分析: scene={context.scene_id}, execution={execution_id}")

        # 1. 读取数据文件结构
        data_file, data_preview = self._resolve_data_file(context)
        if not data_file:
            raise ValueError("未找到可分析的数据文件，请上传 CSV 或 Excel 文件")

        # 2. 构建 prompt
        system_prompt = self.get_prompt_template()
        user_prompt = (
            f"用户需求: {context.user_input}\n\n"
            f"数据文件路径: {data_file}\n\n"
            f"数据预览（前 10 行）:\n```\n{data_preview}\n```\n\n"
            f"请生成数据分析脚本。"
        )

        # 3. 调用 LLM 生成脚本
        logger.info("[数据分析策略] 调用 LLM 生成分析脚本...")
        try:
            raw_response = await call_llm(prompt=user_prompt, system_prompt=system_prompt)
        except Exception as e:
            logger.error(f"[数据分析策略] LLM 调用失败: {e}")
            raise RuntimeError(f"分析脚本生成失败: {e}") from e

        # 4. 清理脚本（去除 markdown 代码块标记）
        script_code = self._clean_script(raw_response)

        # 保存脚本用于调试
        script_path = output_dir / "analysis_script.py"
        script_path.write_text(script_code, encoding="utf-8")
        logger.info(f"[数据分析策略] 分析脚本已保存: {script_path}")

        # 5. 注入变量并执行脚本
        full_script = (
            f"import os\n"
            f"DATA_FILE = r'{data_file}'\n"
            f"OUTPUT_DIR = r'{output_dir}'\n"
            f"os.makedirs(OUTPUT_DIR, exist_ok=True)\n\n"
            f"{script_code}"
        )
        self._run_script(full_script, output_dir)

        # 6. 收集产出文件
        generated_files = sorted(output_dir.glob("*"))
        chart_files = sorted(output_dir.glob("*.png"))
        report_path = output_dir / "report.md"

        # 如果 LLM 没有生成 report.md，手动生成一份
        if not report_path.exists():
            report_content = self._build_fallback_report(
                context.user_input, data_file, chart_files
            )
            report_path.write_text(report_content, encoding="utf-8")
            generated_files = sorted(output_dir.glob("*"))

        # 读取报告预览
        report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
        preview_text = report_text[:500]
        if len(report_text) > 500:
            preview_text += "\n\n..."

        title = f"数据分析报告 - {context.user_input[:30]}"

        logger.info(f"[数据分析策略] 完成，生成 {len(generated_files)} 个文件")

        return CreativeArtifact(
            title=title,
            description=f"基于数据文件的数据分析报告",
            files=[Path(f) for f in generated_files],
            output_type="markdown",
            preview_text=preview_text,
        )

    # ── 内部方法 ────────────────────────────────────

    def _resolve_data_file(self, context: CreativeContext) -> tuple[str | None, str]:
        """解析数据文件并返回 (文件路径, 数据预览)"""
        # 优先使用用户上传的文件
        for fp in context.input_files:
            path = Path(fp)
            if not path.exists():
                continue
            if path.suffix.lower() in (".csv", ".xlsx", ".xls"):
                preview = self._preview_data(path)
                return str(path), preview

        # 如果用户没有上传文件但 input_text 中提到了文件路径
        # 尝试在常见位置查找
        return None, ""

    def _preview_data(self, file_path: Path) -> str:
        """生成数据预览（前 10 行 + 列信息）"""
        try:
            import pandas as pd

            if file_path.suffix.lower() == ".csv":
                df = pd.read_csv(file_path, nrows=10)
            else:
                df = pd.read_excel(file_path, nrows=10)

            info_lines = [
                f"列名: {list(df.columns)}",
                f"数据类型: {dict(df.dtypes.astype(str))}",
                f"行数: {len(df)} (预览前 10 行)",
                "",
                df.to_string(index=False),
            ]
            return "\n".join(info_lines)
        except Exception as e:
            logger.warning(f"[数据分析策略] 数据预览失败: {e}")
            return f"无法预览数据: {e}"

    def _clean_script(self, raw: str) -> str:
        """清理 LLM 返回的脚本，去除 markdown 代码块"""
        text = raw.strip()
        # 去除 ```python ... ``` 包裹
        if text.startswith("```"):
            lines = text.split("\n")
            # 去掉第一行（```python 或 ```）
            lines = lines[1:]
            # 去掉最后一行的 ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)
        return text.strip()

    def _run_script(self, script: str, output_dir: Path):
        """在子进程中执行 Python 脚本"""
        # 写入临时文件执行
        script_file = output_dir / "_runner.py"
        script_file.write_text(script, encoding="utf-8")

        try:
            result = subprocess.run(
                [sys.executable, str(script_file)],
                capture_output=True,
                text=True,
                timeout=SCRIPT_TIMEOUT,
                cwd=str(output_dir),
            )
            if result.returncode != 0:
                logger.error(f"[数据分析策略] 脚本执行失败:\nstdout={result.stdout}\nstderr={result.stderr}")
                raise RuntimeError(
                    f"分析脚本执行失败:\n{result.stderr[:500]}"
                )
            else:
                logger.info(f"[数据分析策略] 脚本执行成功")
                if result.stdout:
                    logger.debug(f"[数据分析策略] stdout: {result.stdout[:200]}")
        except subprocess.TimeoutExpired:
            logger.error(f"[数据分析策略] 脚本执行超时 ({SCRIPT_TIMEOUT}s)")
            raise RuntimeError(f"分析脚本执行超时（{SCRIPT_TIMEOUT}秒）")
        finally:
            # 清理临时脚本
            script_file.unlink(missing_ok=True)

    def _build_fallback_report(self, user_input: str, data_file: str,
                                chart_files: list[Path]) -> str:
        """当 LLM 脚本未生成 report.md 时，构建兜底报告"""
        lines = [
            f"# 数据分析报告",
            "",
            f"## 分析需求",
            f"{user_input}",
            "",
            f"## 数据来源",
            f"`{data_file}`",
            "",
        ]
        if chart_files:
            lines.append("## 分析图表")
            lines.append("")
            for i, cf in enumerate(chart_files, 1):
                lines.append(f"### 图表 {i}")
                lines.append(f"![图表 {i}]({cf.name})")
                lines.append("")
        lines.append("## 说明")
        lines.append("本报告由 AI 自动生成，图表基于上传数据计算得出。")
        return "\n".join(lines)
