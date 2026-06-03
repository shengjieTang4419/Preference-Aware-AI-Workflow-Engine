"""制品Skill执行器

单个Skill的执行引擎。根据SKILL.md中的execution配置选择执行方式。
"""

import asyncio
import json
import logging
import os
import re
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from crewai_web.web.config import ARTIFACTS_DIR, STORAGE_DIR
from crewai_web.web.services.llm_service import call_llm
from crewai_web.web.services.skills.skill_scanner import SkillScanner
from crewai_web.web.services.skills.skill_metadata_parser import SkillMetadataParser
from crewai_web.web.domain.artifact import SkillResult

logger = logging.getLogger(__name__)

# Skill搜索目录
SKILL_SEARCH_DIRS = [
    Path.home() / ".agents" / "skills",
    Path.home() / ".hermes" / "skills",
    Path(__file__).parent.parent.parent.parent / "skills",  # 项目内 skills/
]


class SkillExecutor:
    """单个Skill执行器

    执行流程:
    1. 加载SKILL.md (读取metadata + 内容)
    2. 根据execution.mode选择执行方式:
       - llm_script: LLM生成脚本 → 执行脚本
       - subprocess: 直接执行skill自带的scripts/
       - api_call: 调外部API (TODO)
    3. 返回SkillResult
    """

    def __init__(self):
        self.parser = SkillMetadataParser()
        self.output_dir: Path = Path()

    async def execute(
        self,
        skill_name: str,
        input_data: str,
        execution_id: str,
        output_format: str = "",
        context_files: list[str] | None = None,
        ocr_texts: list[str] | None = None,
    ) -> SkillResult:
        """执行单个Skill

        Args:
            skill_name: Skill名称
            input_data: 输入文本 (上一步输出或用户输入)
            execution_id: 执行ID
            output_format: 输出格式（从 scene_config + AI判断，如 docx/markdown/pptx）
            context_files: 上传的文件路径列表
            ocr_texts: OCR识别文本
        """
        logger.info(f"[SkillExecutor] 开始执行: skill={skill_name}")

        # 1. 加载SKILL.md
        skill_info = self._load_skill(skill_name)
        if not skill_info:
            return SkillResult(
                skill_name=skill_name,
                success=False,
                error_message=f"Skill '{skill_name}' 未找到",
            )

        metadata = skill_info["metadata"]
        content = skill_info["content"]

        # 2. 确定执行模式
        execution_config = metadata.get("execution", {})
        if isinstance(execution_config, str):
            execution_config = {}

        mode = execution_config.get("mode", "llm_script")

        # 3. 创建输出目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        exec_short = execution_id[:12]
        self.output_dir = ARTIFACTS_DIR / f"{timestamp}_{exec_short}" / skill_name
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 4. 执行
        # 存储 output_format（从 pipeline 传入，优先于 metadata）
        self._output_format = output_format or metadata.get("output_type", "")

        try:
            if mode == "llm_script":
                return await self._execute_llm_script(
                    skill_name, content, metadata, input_data,
                    context_files, ocr_texts,
                )
            elif mode == "subprocess":
                return await self._execute_subprocess(
                    skill_name, metadata, input_data,
                )
            elif mode == "api_call":
                return SkillResult(
                    skill_name=skill_name,
                    success=False,
                    error_message="api_call 模式暂未实现",
                )
            else:
                return SkillResult(
                    skill_name=skill_name,
                    success=False,
                    error_message=f"未知执行模式: {mode}",
                )
        except Exception as e:
            logger.error(f"[SkillExecutor] 执行失败: {e}")
            return SkillResult(
                skill_name=skill_name,
                success=False,
                error_message=str(e),
            )

    # ── llm_script 模式 ──────────────────────────────

    async def _execute_llm_script(
        self,
        skill_name: str,
        skill_content: str,
        metadata: dict,
        input_data: str,
        context_files: list[str],
        ocr_texts: list[str],
    ) -> SkillResult:
        """LLM生成脚本 → 执行脚本"""
        # 构建system prompt: SKILL.md内容 + 执行指令
        system_prompt = self._build_system_prompt(skill_name, skill_content, metadata)

        # 构建user prompt: 用户输入 + 文件内容 + OCR
        user_prompt = self._build_user_prompt(input_data, context_files, ocr_texts)

        # 调用LLM
        logger.info(f"[SkillExecutor] 调用LLM生成脚本: skill={skill_name}")
        try:
            raw_response = await call_llm(prompt=user_prompt, system_prompt=system_prompt)
        except Exception as e:
            return SkillResult(
                skill_name=skill_name,
                success=False,
                error_message=f"LLM调用失败: {e}",
            )

        # 清理脚本
        script_code = self._clean_script(raw_response)

        # 判断输出类型：用 pipeline 传入的 output_format（从 scene_config + AI判断）
        # fallback: metadata 中的 output_type（从 SKILL.md 或 installed.json 推断）
        output_type = self._output_format or metadata.get("output_type", "")

        # 非文件输出类型 → 直接返回文本，不执行脚本
        FILE_OUTPUT_TYPES = {"pptx", "docx", "xlsx", "pdf", "mp4", "mp3", "html", "zip"}
        if output_type not in FILE_OUTPUT_TYPES:
            return SkillResult(
                skill_name=skill_name,
                success=True,
                output_text=script_code,
                output_files=[],
            )

        runtime = metadata.get("execution", {})
        if isinstance(runtime, str):
            runtime = {}
        runtime = runtime.get("runtime", "auto")

        # 保存并执行脚本
        if runtime == "auto":
            runtime = self._detect_runtime(script_code, output_type)

        if runtime == "node":
            return await self._run_node_script(skill_name, script_code, output_type)
        elif runtime == "python":
            return await self._run_python_script(skill_name, script_code, output_type)
        else:
            return SkillResult(
                skill_name=skill_name,
                success=True,
                output_text=script_code,
                output_files=[],
            )

    def _build_system_prompt(self, skill_name: str, content: str, metadata: dict) -> str:
        """构建LLM system prompt"""
        # 优先用 pipeline 传入的 output_format，fallback 到 metadata
        output_type = self._output_format or metadata.get("output_type", "")

        prompt_parts = [
            f"# {skill_name} Skill",
            "",
            content,
            "",
            "---",
            "",
            "## 输出要求",
            "",
        ]

        FILE_FORMATS = {"pptx", "docx", "xlsx", "pdf", "html", "zip"}
        if output_type in FILE_FORMATS:
            prompt_parts.extend([
                f"请生成一个完整的脚本来创建 {output_type} 文件。",
                "脚本必须完整可运行，不要添加解释。",
                f"文件路径从 process.argv[2] 读取（Node.js）或 sys.argv[1] 读取（Python）。",
            ])
        elif output_type in ("mp4", "mp3"):
            prompt_parts.extend([
                f"请生成一个脚本来创建 {output_type} 媒体文件。",
                "脚本必须完整可运行，不要添加解释。",
            ])
        else:
            prompt_parts.extend([
                "请直接输出结果内容，不要添加额外的解释。",
            ])

        return "\n".join(prompt_parts)

    def _build_user_prompt(
        self, input_data: str, context_files: list[str], ocr_texts: list[str]
    ) -> str:
        """构建LLM user prompt"""
        parts = [input_data]

        if context_files:
            file_contents = self._read_files(context_files)
            if file_contents:
                parts.append("\n---\n参考文件内容:\n")
                parts.append(file_contents)

        if ocr_texts:
            parts.append("\n---\n图片OCR识别结果:\n")
            for i, text in enumerate(ocr_texts):
                if text.strip():
                    parts.append(f"### 图片 {i+1}\n{text}")

        return "\n".join(parts)

    # ── 脚本执行 ──────────────────────────────────────

    async def _run_node_script(
        self, skill_name: str, script_code: str, output_type: str
    ) -> SkillResult:
        """执行Node.js脚本"""
        script_path = self.output_dir / f"generate_{skill_name}.js"
        script_path.write_text(script_code, encoding="utf-8")

        ext = output_type or "txt"
        output_path = self.output_dir / f"output.{ext}"

        env = os.environ.copy()
        env["NODE_PATH"] = "/opt/homebrew/lib/node_modules"

        try:
            proc = await asyncio.create_subprocess_exec(
                "node", str(script_path), str(output_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.output_dir),
                env=env,
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return SkillResult(
                    skill_name=skill_name,
                    success=False,
                    error_message="脚本执行超时（120秒）",
                )

            if proc.returncode != 0:
                error_msg = stderr.decode().strip()
                return SkillResult(
                    skill_name=skill_name,
                    success=False,
                    error_message=f"脚本执行失败:\n{error_msg[:500]}",
                )

            output_files = []
            if output_path.exists():
                output_files.append(str(output_path))

            return SkillResult(
                skill_name=skill_name,
                success=True,
                output_text=stdout.decode().strip() if stdout else "",
                output_files=output_files,
            )
        except FileNotFoundError:
            return SkillResult(
                skill_name=skill_name,
                success=False,
                error_message="未找到 node 命令",
            )

    async def _run_python_script(
        self, skill_name: str, script_code: str, output_type: str
    ) -> SkillResult:
        """执行Python脚本"""
        script_path = self.output_dir / f"generate_{skill_name}.py"
        script_path.write_text(script_code, encoding="utf-8")

        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, str(script_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.output_dir),
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return SkillResult(
                    skill_name=skill_name,
                    success=False,
                    error_message="脚本执行超时（120秒）",
                )

            if proc.returncode != 0:
                error_msg = stderr.decode().strip()
                return SkillResult(
                    skill_name=skill_name,
                    success=False,
                    error_message=f"脚本执行失败:\n{error_msg[:500]}",
                )

            # 收集输出文件
            output_files = []
            for f in sorted(self.output_dir.glob("*")):
                if f.is_file() and not f.name.startswith("_"):
                    output_files.append(str(f))

            return SkillResult(
                skill_name=skill_name,
                success=True,
                output_text=stdout.decode().strip() if stdout else "",
                output_files=output_files,
            )
        except FileNotFoundError:
            return SkillResult(
                skill_name=skill_name,
                success=False,
                error_message="未找到 python 命令",
            )

    # ── subprocess 模式 ──────────────────────────────

    async def _execute_subprocess(
        self, skill_name: str, metadata: dict, input_data: str
    ) -> SkillResult:
        """直接执行skill自带的scripts/"""
        # 查找skill目录
        skill_dir = self._find_skill_dir(skill_name)
        if not skill_dir:
            return SkillResult(
                skill_name=skill_name,
                success=False,
                error_message=f"Skill目录 '{skill_name}' 未找到",
            )

        scripts_dir = skill_dir / "scripts"
        if not scripts_dir.exists():
            return SkillResult(
                skill_name=skill_name,
                success=False,
                error_message=f"Skill '{skill_name}' 没有 scripts/ 目录",
            )

        # 找入口脚本
        execution = metadata.get("execution", {})
        if isinstance(execution, str):
            execution = {}
        entrypoint = execution.get("entrypoint", "")

        if not entrypoint:
            # 找第一个 .py 或 .js
            for ext in ("*.py", "*.js"):
                found = list(scripts_dir.glob(ext))
                if found:
                    entrypoint = found[0].name
                    break

        if not entrypoint:
            return SkillResult(
                skill_name=skill_name,
                success=False,
                error_message=f"Skill '{skill_name}' 没有可执行脚本",
            )

        script_path = scripts_dir / entrypoint
        if not script_path.exists():
            return SkillResult(
                skill_name=skill_name,
                success=False,
                error_message=f"入口脚本不存在: {script_path}",
            )

        # 写入输入数据到临时文件
        input_file = self.output_dir / "_input.txt"
        input_file.write_text(input_data, encoding="utf-8")

        # 执行
        if entrypoint.endswith(".py"):
            cmd = [sys.executable, str(script_path)]
        elif entrypoint.endswith(".js"):
            cmd = ["node", str(script_path)]
        else:
            return SkillResult(
                skill_name=skill_name,
                success=False,
                error_message=f"不支持的脚本类型: {entrypoint}",
            )

        env = os.environ.copy()
        env["SKILL_INPUT"] = str(input_file)
        env["SKILL_OUTPUT_DIR"] = str(self.output_dir)
        env["NODE_PATH"] = "/opt/homebrew/lib/node_modules"

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.output_dir),
                env=env,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)

            if proc.returncode != 0:
                return SkillResult(
                    skill_name=skill_name,
                    success=False,
                    error_message=stderr.decode().strip()[:500],
                )

            output_files = []
            for f in sorted(self.output_dir.glob("*")):
                if f.is_file() and not f.name.startswith("_"):
                    output_files.append(str(f))

            return SkillResult(
                skill_name=skill_name,
                success=True,
                output_text=stdout.decode().strip() if stdout else "",
                output_files=output_files,
            )
        except Exception as e:
            return SkillResult(
                skill_name=skill_name,
                success=False,
                error_message=str(e),
            )

    # ── 工具方法 ──────────────────────────────────────

    def _load_skill(self, skill_name: str) -> Optional[dict]:
        """加载Skill (从多个搜索目录)"""
        # 1. 先从已安装列表查找
        installed = self._load_installed_skill(skill_name)
        if installed:
            return installed

        # 2. 从搜索目录查找
        for search_dir in SKILL_SEARCH_DIRS:
            skill_dir = search_dir / skill_name
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                return {
                    "metadata": self.parser.parse(skill_md),
                    "content": skill_md.read_text(encoding="utf-8"),
                    "path": str(skill_md),
                }

        return None

    def _load_installed_skill(self, skill_name: str) -> Optional[dict]:
        """从installed.json加载已安装的skill"""
        installed_file = STORAGE_DIR / "skills" / "installed.json"
        if not installed_file.exists():
            return None

        try:
            skills = json.loads(installed_file.read_text(encoding="utf-8"))
            for s in skills:
                if s.get("name") == skill_name:
                    raw_content = s.get("raw_content", "")
                    # 解析metadata
                    metadata = {}
                    if raw_content.startswith("---"):
                        parts = raw_content.split("---", 2)
                        if len(parts) >= 3:
                            metadata = self.parser._parse_frontmatter(parts[1].strip())
                    metadata.setdefault("type", "artifact" if s.get("output_type") else "tool")
                    # 如果 frontmatter 没有 output_type，从 skill 名称推断
                    inferred_output_type = _infer_output_type_from_name(skill_name)
                    metadata.setdefault("output_type", inferred_output_type)
                    metadata.setdefault("execution", {})
                    return {
                        "metadata": metadata,
                        "content": raw_content,
                        "path": f"installed:{skill_name}",
                    }
        except Exception as e:
            logger.warning(f"[SkillExecutor] 加载已安装skill失败: {e}")

        return None

    def _find_skill_dir(self, skill_name: str) -> Optional[Path]:
        """查找Skill目录"""
        for search_dir in SKILL_SEARCH_DIRS:
            skill_dir = search_dir / skill_name
            if skill_dir.exists():
                return skill_dir
        return None

    def _detect_runtime(self, script_code: str, output_type: str) -> str:
        """自动检测脚本运行时"""
        if "require(" in script_code or "module.exports" in script_code:
            return "node"
        if "import " in script_code or "def " in script_code or "print(" in script_code:
            return "python"
        # pptxgenjs 是 Node.js 生态
        if output_type == "pptx":
            return "node"
        return "python"

    def _clean_script(self, raw: str) -> str:
        """清理LLM返回的脚本"""
        text = raw.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)
        return text.strip()

    def _read_files(self, file_paths: list[str]) -> str:
        """读取文件内容"""
        contents = []
        for fp in file_paths:
            path = Path(fp)
            if not path.exists():
                continue
            try:
                text = path.read_text(encoding="utf-8")
                contents.append(f"### 文件: {path.name}\n\n{text}")
            except Exception as e:
                logger.warning(f"[SkillExecutor] 读取文件失败 {fp}: {e}")
        return "\n\n".join(contents)


# 全局单例
_skill_executor: Optional[SkillExecutor] = None


def _infer_output_type_from_name(name: str) -> str:
    """从 skill 名称推断输出类型"""
    name_lower = name.lower()
    if "pptx" in name_lower or "ppt" in name_lower:
        return "pptx"
    if "docx" in name_lower or "document" in name_lower:
        return "docx"
    if "xlsx" in name_lower or "excel" in name_lower:
        return "xlsx"
    if "pdf" in name_lower:
        return "pdf"
    if "mp4" in name_lower or "video" in name_lower:
        return "mp4"
    if "mp3" in name_lower or "music" in name_lower:
        return "mp3"
    return ""


def get_skill_executor() -> SkillExecutor:
    """获取Skill执行器单例"""
    global _skill_executor
    if _skill_executor is None:
        _skill_executor = SkillExecutor()
    return _skill_executor
