"""LLM 调试服务，用于保存请求/响应信息"""

import logging
from pathlib import Path


class DebugService:
    """调试服务，用于保存LLM请求/响应信息"""

    def __init__(self, debug_enabled: bool = False, debug_dir: str | None = None) -> None:
        self.debug_enabled = debug_enabled
        self.debug_dir = debug_dir
        self.logger = logging.getLogger(__name__)

    def new_trace_id(self) -> str:
        """生成一次 LLM 调用对应的 trace_id，用于将多份调试文件关联在一起"""
        import time

        return time.strftime("%Y%m%d-%H%M%S") + f"_{int(time.time() * 1000) % 1000:03d}"

    def save_debug_info(
        self,
        system_prompt: str,
        user_prompt: str,
        response: str | None = None,
        schema: dict | None = None,
        *,
        trace_id: str | None = None,
    ) -> None:
        """保存调试信息到文件"""
        if not self.debug_enabled:
            return

        ts = trace_id or self.new_trace_id()

        if self.debug_dir and str(self.debug_dir).strip():
            debug_dir = Path(str(self.debug_dir))
        else:
            debug_dir = Path(__file__).resolve().parents[2] / ".local" / "llm_debug"

        self.logger.info("LLM DEBUG write: dir=%s trace_id=%s", debug_dir, ts)

        debug_dir.mkdir(parents=True, exist_ok=True)

        (debug_dir / f"system_prompt_{ts}.txt").write_text(system_prompt, encoding="utf-8")
        (debug_dir / f"user_prompt_{ts}.txt").write_text(user_prompt, encoding="utf-8")

        if response is not None:
            (debug_dir / f"response_{ts}.txt").write_text(response, encoding="utf-8")
        if schema is not None:
            import json

            (debug_dir / f"schema_{ts}.json").write_text(
                json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8"
            )

    def is_debug_enabled(self) -> bool:
        """检查是否启用调试模式"""
        return self.debug_enabled
    
    def log_prompt(self, prompt: str, role: str | None = None, model: str | None = None) -> None:
        """记录 prompt（用于 AIClient）"""
        if not self.debug_enabled:
            return
        
        trace_id = self.new_trace_id()
        role_prefix = f"[{role}] " if role else ""
        model_info = f" model={model}" if model else ""
        
        self.logger.info(f"{role_prefix}LLM Prompt (trace_id={trace_id}{model_info}):\n{prompt[:200]}...")
        
        # 保存到文件
        if self.debug_dir and str(self.debug_dir).strip():
            debug_dir = Path(str(self.debug_dir))
        else:
            debug_dir = Path(__file__).resolve().parents[2] / ".local" / "llm_debug"
        
        debug_dir.mkdir(parents=True, exist_ok=True)
        
        # 在文件开头添加模型信息
        content = f"# Model: {model}\n# Trace ID: {trace_id}\n# Role: {role or 'N/A'}\n\n{prompt}"
        (debug_dir / f"prompt_{trace_id}.txt").write_text(content, encoding="utf-8")
    
    def log_response(self, response: str, elapsed: float = 0, role: str | None = None, model: str | None = None) -> None:
        """记录 response（用于 AIClient）"""
        if not self.debug_enabled:
            return
        
        trace_id = self.new_trace_id()
        role_prefix = f"[{role}] " if role else ""
        model_info = f" model={model}" if model else ""
        
        self.logger.info(
            f"{role_prefix}LLM Response (trace_id={trace_id}, elapsed={elapsed:.2f}s{model_info}):\n{response[:200]}..."
        )
        
        # 保存到文件
        if self.debug_dir and str(self.debug_dir).strip():
            debug_dir = Path(str(self.debug_dir))
        else:
            debug_dir = Path(__file__).resolve().parents[2] / ".local" / "llm_debug"
        
        debug_dir.mkdir(parents=True, exist_ok=True)
        
        # 在文件开头添加模型信息
        content = f"# Model: {model}\n# Trace ID: {trace_id}\n# Role: {role or 'N/A'}\n# Elapsed: {elapsed:.2f}s\n\n{response}"
        (debug_dir / f"response_{trace_id}.txt").write_text(content, encoding="utf-8")
