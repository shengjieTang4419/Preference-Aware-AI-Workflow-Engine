#!/usr/bin/env python3
"""Web server entry point"""

import uvicorn
from pathlib import Path
import sys

# 添加项目根到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def main():
    """Web 服务入口"""
    print("🌐 Starting CrewAI Web Server...")
    print("📍 URL: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop\n")
    
    uvicorn.run(
        "crewai_web.web.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(Path(__file__).parent)],
    )


if __name__ == "__main__":
    main()
