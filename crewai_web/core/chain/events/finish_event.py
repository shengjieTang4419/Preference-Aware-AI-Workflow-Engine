"""
FinishEvent - 完成事件

责任链收尾节点，负责：
1. 保存执行结果到文件
2. 生成 README.md
3. 保存 metadata
4. 汇总指标
"""

import json
import time
from pathlib import Path

from crewai_web.core.chain.events.base_event import BaseEvent, EventType, ExecutionContext


class FinishEvent(BaseEvent):
    """完成事件 - 汇总记录"""
    
    def __init__(self):
        super().__init__(EventType.STANDARD)
    
    def handle(self, ctx: ExecutionContext) -> ExecutionContext:
        ctx.log("INFO", "[Finish] Starting post-execution processing")
        
        if not ctx.output_dir:
            ctx.log("WARNING", "[Finish] No output_dir specified, skipping file output")
            return ctx
        
        output_path = Path(ctx.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 1. 保存执行结果
        if ctx.result:
            (output_path / "result.txt").write_text(ctx.result, encoding="utf-8")
            ctx.log("INFO", f"[Finish] Result saved ({len(ctx.result)} chars)")
        
        # 2. 生成 README.md
        crew_name = ctx.crew_config.name if ctx.crew_config else ctx.crew_id
        duration = ctx.duration_seconds
        
        readme = f"""# Execution Summary

- **Execution ID**: {ctx.exec_id}
- **Requirement**: {ctx.requirement}
- **Crew**: {crew_name}
- **Status**: {"COMPLETED" if ctx.success else "FAILED"}
- **Duration**: {f"{duration:.2f}s" if duration else "N/A"}
- **Output Directory**: {ctx.output_dir}

## Metrics

- Tasks started: {ctx.metrics.get("task_started", 0)}
- Tasks completed: {ctx.metrics.get("task_completed", 0)}
- Tasks failed: {ctx.metrics.get("task_failed", 0)}

## Result

{ctx.result or "No result"}
"""
        (output_path / "README.md").write_text(readme, encoding="utf-8")
        ctx.log("INFO", "[Finish] README.md generated")
        
        # 3. 保存 metadata
        metadata = {
            "execution_id": ctx.exec_id,
            "requirement": ctx.requirement,
            "input_folder": ctx.input_folder,
            "crew_id": ctx.crew_id,
            "completed_at": str(time.time()),
            "process_type": ctx.crew_config.process_type if ctx.crew_config else "unknown",
            "success": ctx.success,
            "duration_seconds": duration,
            "metrics": {
                k: str(v) if not isinstance(v, (int, float, bool, type(None))) else v
                for k, v in ctx.metrics.items()
            },
        }
        (output_path / ".metadata.json").write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        ctx.log("INFO", "[Finish] Metadata saved")
        
        # 4. 保存日志
        (output_path / "chain.log").write_text(
            "\n".join(ctx.logs), encoding="utf-8"
        )
        
        # 5. 准备偏好进化上下文（轻量级）
        if ctx.success:
            self._prepare_evolution_context(ctx)
        
        ctx.log("INFO", "[Finish] ✅ Post-execution processing completed")
        
        return ctx
    
    def _prepare_evolution_context(self, ctx: ExecutionContext) -> None:
        """
        准备偏好进化上下文（轻量级）
        
        只记录用户真正的偏好：
        1. 用户原始输入（scenario + context）
        2. 执行是否成功
        3. 简要的执行摘要（不是完整结果）
        """
        try:
            ctx.extras["evolution_context"] = {
                "exec_id": ctx.exec_id,
                "exec_topic": ctx.crew_config.name if ctx.crew_config else ctx.crew_id,
                
                # 用户偏好：原始输入
                "user_input": {
                    "requirement": ctx.requirement,
                    "inputs": ctx.inputs,
                },
                
                # 执行结果：只要成功/失败 + 简要摘要
                "execution_summary": {
                    "success": ctx.success,
                    "duration_seconds": ctx.duration_seconds,
                    "task_count": len(ctx.task_configs),
                    "error": ctx.error if not ctx.success else None,
                },
                
                # 用户干预（如果有手动修改）
                "user_interventions": ctx.extras.get("user_interventions", []),
            }
            ctx.log("INFO", "[Finish] Evolution context prepared (lightweight)")
            
        except Exception as e:
            ctx.log("WARNING", f"[Finish] Failed to prepare evolution context: {e}")
