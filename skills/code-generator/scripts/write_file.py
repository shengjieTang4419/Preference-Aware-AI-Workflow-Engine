"""
文件写入工具
将生成的代码写入到指定文件
"""
import json
from pathlib import Path

# Tool 元数据
TOOL_NAME = "write_code_file"
TOOL_DESCRIPTION = "将生成的代码写入到指定文件路径，自动创建目录"


def run(input: str) -> str:
    """
    执行文件写入
    
    Args:
        input: JSON 字符串，格式: {"file_path": "相对路径", "content": "文件内容"}
    
    Returns:
        执行结果描述
    """
    try:
        # 解析输入
        data = json.loads(input)
        file_path = data.get("file_path")
        content = data.get("content")
        
        if not file_path or not content:
            return "错误: 缺少 file_path 或 content 参数"
        
        # 确定输出目录（默认为当前执行的 output_dir）
        # 这里简化处理，实际应该从环境变量或配置获取
        output_base = Path("/tmp/crew_output")  # 临时目录，实际应该动态获取
        output_base.mkdir(parents=True, exist_ok=True)
        
        # 构建完整路径
        full_path = output_base / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入文件
        full_path.write_text(content, encoding="utf-8")
        
        return f"✅ 文件已写入: {full_path} ({len(content)} 字符)"
    
    except json.JSONDecodeError as e:
        return f"错误: 无法解析 JSON 输入 - {e}"
    except Exception as e:
        return f"错误: 写入文件失败 - {e}"


# 用于测试
if __name__ == "__main__":
    test_input = json.dumps({
        "file_path": "test/example.py",
        "content": "print('Hello, World!')"
    })
    print(run(test_input))
