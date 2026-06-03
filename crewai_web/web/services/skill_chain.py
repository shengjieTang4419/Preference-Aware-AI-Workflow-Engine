"""制品Skill链路编排

多个Skill的链式执行编排。前一个Skill的输出作为后一个的输入。
"""

import logging
from typing import List, Optional

from crewai_web.web.services.skill_executor import get_skill_executor, SkillExecutor
from crewai_web.web.services import artifact_execution_service
from crewai_web.web.domain.artifact import (
    SkillResult,
    ArtifactResult,
    ArtifactSkillExecCreate,
    ArtifactSkillExecUpdate,
)

logger = logging.getLogger(__name__)


class SkillChain:
    """多Skill链路编排

    执行流程:
    1. 按顺序执行skills (前一个输出 → 后一个输入)
    2. 每个skill的执行记录写入 artifact_skill_executions 表
    3. 最终结果合并为 ArtifactResult
    """

    def __init__(self):
        self.executor = get_skill_executor()

    async def execute(
        self,
        skill_names: List[str],
        crew_output: str,
        execution_id: str,
        scene_id: str = "",
        output_format: str = "",
        context_files: list[str] | None = None,
        ocr_texts: list[str] | None = None,
    ) -> ArtifactResult:
        """执行Skill链

        Args:
            skill_names: Skill名称列表（按执行顺序）
            crew_output: Crew执行的文本输出（第一个skill的输入）
            execution_id: 执行ID
            scene_id: 场景ID
            output_format: 输出格式（从 scene_config + AI判断，如 docx/markdown/pptx）
            context_files: 上传的文件路径
            ocr_texts: OCR文本
        """
        if not skill_names:
            return ArtifactResult(
                skill_chain=[],
                success=False,
                error_message="没有指定任何Skill",
            )

        logger.info(f"[SkillChain] 开始执行链路: skills={skill_names}")

        chain_results: List[SkillResult] = []
        current_input = crew_output

        for i, skill_name in enumerate(skill_names):
            logger.info(f"[SkillChain] 执行 Step {i+1}/{len(skill_names)}: {skill_name}")

            # 创建执行记录
            record = await artifact_execution_service.create_exec_record(
                ArtifactSkillExecCreate(
                    execution_id=execution_id,
                    skill_name=skill_name,
                    step_index=i,
                )
            )

            # 更新状态为running
            await artifact_execution_service.update_exec_record(
                record.id,
                ArtifactSkillExecUpdate(
                    status="running",
                    input_summary=current_input[:500] if current_input else "",
                ),
            )

            # 执行skill
            result = await self.executor.execute(
                skill_name=skill_name,
                input_data=current_input,
                execution_id=execution_id,
                output_format=output_format,
                context_files=context_files if i == 0 else None,  # 只有第一个skill用原始文件
                ocr_texts=ocr_texts if i == 0 else None,
            )

            chain_results.append(result)

            # 更新执行记录
            if result.success:
                await artifact_execution_service.update_exec_record(
                    record.id,
                    ArtifactSkillExecUpdate(
                        status="completed",
                        output_files=result.output_files,
                        output_metadata=result.output_metadata,
                    ),
                )
                # 下一个skill的输入 = 当前skill的文本输出
                # 如果没有文本输出，用上一步的输入
                current_input = result.output_text or current_input
            else:
                await artifact_execution_service.update_exec_record(
                    record.id,
                    ArtifactSkillExecUpdate(
                        status="failed",
                        error_message=result.error_message,
                    ),
                )
                # 链路中断
                return ArtifactResult(
                    skill_chain=skill_names,
                    success=False,
                    error_message=f"Skill '{skill_name}' 执行失败: {result.error_message}",
                )

        # 汇总结果
        all_output_files = []
        for r in chain_results:
            all_output_files.extend(r.output_files)

        # 输出类型: 优先用 pipeline 传入的 output_format
        output_type = output_format

        # fallback: 最后一个成功 skill 的 output_type
        if not output_type:
            last_metadata = chain_results[-1].output_metadata if chain_results else {}
            output_type = last_metadata.get("output_type", "")

        # 最终 fallback: 从 skill 名称推断
        if not output_type:
            output_type = self._infer_output_type(skill_names)

        return ArtifactResult(
            skill_chain=skill_names,
            success=True,
            title=self._extract_title(crew_output),
            description=f"通过 {len(skill_names)} 个Skills生成的制品",
            output_type=output_type,
            output_files=all_output_files,
            preview_text=current_input[:500] if current_input else "",
        )

    def _infer_output_type(self, skill_names: List[str]) -> str:
        """从skill名称推断输出类型（仅作为最后 fallback）"""
        name_lower = " ".join(skill_names).lower()
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
        return "markdown"

    def _extract_title(self, text: str) -> str:
        """从文本提取标题"""
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("# "):
                return line.lstrip("# ").strip()
        return text[:30].strip() or "未命名制品"


# 全局单例
_skill_chain: Optional[SkillChain] = None


def get_skill_chain() -> SkillChain:
    """获取Skill链路编排器单例"""
    global _skill_chain
    if _skill_chain is None:
        _skill_chain = SkillChain()
    return _skill_chain
