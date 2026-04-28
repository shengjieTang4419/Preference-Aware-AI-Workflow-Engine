"""
执行结果保存器
"""
import json
import time
from pathlib import Path


class ExecutionResultSaver:
    """执行结果保存器"""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def save_result(
        self,
        exec_id: str,
        requirement: str,
        crew_name: str,
        result_text: str,
        input_folder: str,
        crew_id: str,
        process_type: str,
    ):
        """保存执行结果到文件"""
        # README.md
        readme_content = f"""# Execution Summary

- **Execution ID**: {exec_id}
- **Requirement**: {requirement}
- **Crew**: {crew_name}
- **Status**: COMPLETED
- **Output Directory**: {self.output_dir}

## Result

{result_text}
"""
        (self.output_dir / "README.md").write_text(readme_content, encoding="utf-8")

        # result.txt
        (self.output_dir / "result.txt").write_text(result_text, encoding="utf-8")

        # .metadata.json
        metadata = {
            "execution_id": exec_id,
            "requirement": requirement,
            "input_folder": input_folder,
            "crew_id": crew_id,
            "completed_at": str(time.time()),
            "process_type": process_type,
        }
        (self.output_dir / ".metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
