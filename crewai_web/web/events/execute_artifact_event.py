"""执行制品生成事件 — Pipeline第9步

在Crew执行完成后，调用artifact skills生成最终制品。
output_format 从 scene_config 读取，经 AI 轻量判断后传给 SkillExecutor。
"""

import json
import logging
import re
from crewai_web.core.event import BusinessEvent, EventContext
from crewai_web.web.services.skill_chain import get_skill_chain
from crewai_web.web.services.magic_wand_service import match_artifact_skills
from crewai_web.web.services.scene_config_service import get_config, get_config_by_title
from crewai_web.web.services.llm_service import call_llm

logger = logging.getLogger(__name__)

# 支持的输出格式（不是硬编码映射，是格式白名单）
SUPPORTED_OUTPUT_FORMATS = {
    "markdown", "md", "txt", "text",
    "docx", "doc", "word",
    "pptx", "ppt", "presentation",
    "xlsx", "xls", "excel", "spreadsheet",
    "pdf",
    "html", "htm",
    "mp4", "video",
    "mp3", "audio", "music",
    "zip",
}

# 格式标准化映射（用户口语 → 标准格式）
FORMAT_NORMALIZE_MAP = {
    "word": "docx", "doc": "docx",
    "ppt": "pptx", "presentation": "pptx",
    "excel": "xlsx", "xls": "xlsx", "spreadsheet": "xlsx",
    "md": "markdown", "text": "txt",
    "video": "mp4", "audio": "mp3", "music": "mp3",
}


async def judge_output_format(user_input: str, scene_output_format: str) -> str:
    """AI 轻量判断：根据用户输入 + 场景默认格式，决定最终输出格式

    不会每次调用 LLM，先做关键词快速匹配，命中即返回。
    只有模糊情况才交给 LLM。
    """
    DEFAULT = scene_output_format or "markdown"
    input_lower = user_input.lower()

    # 快速关键词匹配（不调用 LLM）
    keyword_hints = [
        ("word文档", "docx"), ("word", "docx"), (".docx", "docx"), (".doc", "docx"),
        ("ppt", "pptx"), ("幻灯片", "pptx"), ("演示文稿", "pptx"), ("presentation", "pptx"),
        ("excel", "xlsx"), ("表格", "xlsx"), ("电子表格", "xlsx"), ("spreadsheet", "xlsx"),
        ("pdf", "pdf"), (".pdf", "pdf"),
        ("markdown", "markdown"), ("md文件", "markdown"),
        ("txt", "txt"), ("纯文本", "txt"), ("文本文件", "txt"),
        ("视频", "mp4"), ("video", "mp4"), ("mp4", "mp4"),
        ("音乐", "mp3"), ("audio", "mp3"), ("歌曲", "mp3"), ("mp3", "mp3"),
        ("html", "html"), ("网页", "html"),
    ]
    for kw, fmt in keyword_hints:
        if kw in input_lower:
            return fmt

    # 如果没有明确关键词，用 LLM 做轻量判断
    prompt = f"""用户需求: {user_input[:300]}
场景默认输出格式: {scene_output_format}

请判断最终应该用什么格式输出。只回复一个格式名 (docx/markdown/pptx/xlsx/pdf/txt/html/mp4/mp3)。
如果用户没有明确指定格式，就用场景默认的 "{scene_output_format}"。
只回复格式名，不要解释。"""

    try:
        response = await call_llm(prompt=prompt, system_prompt="你是输出格式判断器。只回复一个格式名。")
        fmt = response.strip().lower()
        # 标准化
        fmt = FORMAT_NORMALIZE_MAP.get(fmt, fmt)
        if fmt in SUPPORTED_OUTPUT_FORMATS:
            return fmt
    except Exception as e:
        logger.warning(f"[JudgeFormat] LLM 判断失败: {e}")

    return DEFAULT


class ExecuteArtifactEvent(BusinessEvent):
    """步骤 9: 执行制品生成Skills"""

    name = "生成制品"
    step = 9
    total = 9

    async def do_execute(self, ctx: EventContext) -> None:
        # 1. 获取场景配置（scene_id 优先，fallback 到 title 提取）
        lookup_id = ctx.scene_id or ctx.scenario
        scene_config = await get_config(lookup_id) if lookup_id else None

        if not scene_config and not ctx.scene_id and ctx.scenario:
            m = re.match(r'^\[(.+?)\]', ctx.scenario)
            if m:
                scene_config = await get_config_by_title(m.group(1))

        # 2. 确定输出格式: 从 scene_config 读取，经 AI 轻量判断
        scene_output_format = scene_config.output_format if scene_config else "markdown"
        output_format = await judge_output_format(ctx.scenario, scene_output_format)
        ctx.output_format = output_format
        logger.info(f"[ExecuteArtifact] 输出格式: {output_format} (场景默认={scene_output_format})")

        # 3. 匹配 artifact skills
        scene_artifact_skills = None
        if scene_config and scene_config.artifact_skills:
            scene_artifact_skills = scene_config.artifact_skills

        matched_skills = await match_artifact_skills(
            scene_id=ctx.scenario,
            user_input=ctx.scenario,
            scene_artifact_skills=scene_artifact_skills,
        )

        if not matched_skills:
            logger.info(f"[ExecuteArtifact] 未匹配到artifact skills，跳过制品生成")
            ctx.artifact_skills = []
            return

        skill_names = [s["name"] for s in matched_skills]
        ctx.artifact_skills = skill_names
        logger.info(f"[ExecuteArtifact] 匹配到 {len(skill_names)} 个skills: {skill_names}")

        # 4. 获取Crew输出作为输入
        crew_output = ctx.crew_output or ctx.scenario

        # 5. 执行skill链（传入 output_format）
        chain = get_skill_chain()
        result = await chain.execute(
            skill_names=skill_names,
            crew_output=crew_output,
            execution_id=ctx.execution_id,
            scene_id=ctx.scene_id or ctx.scenario,
            output_format=output_format,
        )

        # 6. 保存结果
        ctx.artifact_result = {
            "skill_chain": result.skill_chain,
            "success": result.success,
            "title": result.title,
            "description": result.description,
            "output_type": result.output_type,
            "output_files": result.output_files,
            "preview_text": result.preview_text,
        }

        if result.success:
            logger.info(f"[ExecuteArtifact] 制品生成成功: {result.title}")
        else:
            logger.error(f"[ExecuteArtifact] 制品生成失败: {result.error_message}")
            ctx.artifact_result["error_message"] = result.error_message
