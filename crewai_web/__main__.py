#!/usr/bin/env python3
"""CLI entry point for CrewAI Web"""

import sys
from pathlib import Path

# 添加项目根到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main():
    """CLI 模式入口"""
    print("🚀 CrewAI Web - CLI Mode")
    print("=" * 50)
    print("\nThis is the legacy CLI entry.")
    print("For web UI, run: python -m crewai_web.web")
    print("\nTo start a crew execution, use the API or web interface.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
