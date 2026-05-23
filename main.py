#!/usr/bin/env python3
"""Web 服务入口点 - 根目录快捷方式

实际调用 crewai_web.web 包内的启动逻辑
"""
import sys
from pathlib import Path

# 确保项目根目录在路径中
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 在导入 app 之前加载 .env，确保 config.py 的 os.getenv() 能读到值
from dotenv import load_dotenv
env_file = project_root / ".env"
if env_file.exists():
    load_dotenv(env_file, override=True)

# 导入并运行 web 模块的 main
from crewai_web.web.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
