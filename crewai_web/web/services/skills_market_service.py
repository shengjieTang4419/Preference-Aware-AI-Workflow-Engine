"""技能发现与管理服务

发现来源: skills.sh API
本地存储: storage/skills/installed.json
"""
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from crewai_web.web.config import STORAGE_DIR
from crewai_web.web.services import llm_service

logger = logging.getLogger(__name__)

SKILLS_DIR = STORAGE_DIR / "skills"
INSTALLED_FILE = SKILLS_DIR / "installed.json"


# ── 本地存储 ──────────────────────────────────────────

def _ensure_dir():
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)


def _load_installed() -> list:
    """读取已安装技能列表"""
    _ensure_dir()
    if not INSTALLED_FILE.exists():
        return []
    with open(INSTALLED_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_installed(skills: list):
    """保存已安装技能列表"""
    _ensure_dir()
    with open(INSTALLED_FILE, "w", encoding="utf-8") as f:
        json.dump(skills, f, indent=2, ensure_ascii=False)


# ── 技能发现 ──────────────────────────────────────────

async def discover_skills(query: str = "", limit: int = 20) -> list:
    """发现热门技能（优先 skills.sh，fallback 本地数据）"""
    all_skills = _fallback_top_skills()

    # 尝试从 skills.sh 获取最新数据
    try:
        import httpx
        async with httpx.AsyncClient(timeout=3) as client:
            resp = await client.get(
                "https://www.skills.sh/api/skills",
                params={"q": query or "", "limit": limit, "sort": "installs"},
            )
            if resp.status_code == 200:
                data = resp.json()
                if data and len(data) > 0:
                    all_skills = data
    except Exception:
        pass  # 使用 fallback

    # 本地过滤
    if query:
        q = query.lower()
        all_skills = [s for s in all_skills if q in s.get("name", "").lower()
                      or q in s.get("description", "").lower()]

    return all_skills[:limit]


def _fallback_top_skills() -> list:
    """离线 fallback: skills.sh 排行榜 top 技能"""
    return [
        {"name": "find-skills", "source": "vercel-labs/skills", "installs": "1.5M",
         "description": "帮助发现和安装 agent 技能的工具"},
        {"name": "frontend-design", "source": "anthropics/skills", "installs": "421K",
         "description": "前端设计最佳实践和 UI/UX 指南"},
        {"name": "vercel-react-best-practices", "source": "vercel-labs/agent-skills", "installs": "389K",
         "description": "React 和 Next.js 性能优化指南"},
        {"name": "web-design-guidelines", "source": "vercel-labs/agent-skills", "installs": "317K",
         "description": "Web 设计规范和最佳实践"},
        {"name": "agent-browser", "source": "vercel-labs/agent-browser", "installs": "281K",
         "description": "浏览器自动化技能"},
        {"name": "remotion-best-practices", "source": "remotion-dev/skills", "installs": "299K",
         "description": "Remotion 视频生成最佳实践"},
    ]


# ── 技能安装 ──────────────────────────────────────────

async def install_skill(package: str, user_id: Optional[int] = None) -> dict:
    """安装技能并生成 AI 说明

    Args:
        package: 技能包名，如 vercel-labs/skills@find-skills
    """
    installed = _load_installed()

    # 检查是否已安装
    skill_name = package.split("@")[-1] if "@" in package else package.split("/")[-1]
    if any(s["name"] == skill_name for s in installed):
        raise ValueError(f"技能 '{skill_name}' 已安装")

    # 1. 执行 npx skills add（使用 asyncio 避免阻塞事件循环）
    logger.info(f"正在安装技能: {package}")
    proc = await asyncio.create_subprocess_exec(
        "npx", "skills", "add", package, "-g", "-y",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)
    except asyncio.TimeoutError:
        proc.kill()
        raise ValueError(f"安装超时（60秒）")
    if proc.returncode != 0:
        error_msg = (stderr.decode().strip() or stdout.decode().strip())
        raise ValueError(f"安装失败: {error_msg}")

    # 2. 读取技能的 SKILL.md
    skill_content = _read_skill_md(skill_name)

    # 3. 调用 AI 生成结构化说明
    explanation = await _generate_explanation(skill_name, skill_content)

    # 4. 存入本地
    skill_record = {
        "name": skill_name,
        "package": package,
        "installed_at": datetime.utcnow().isoformat(),
        "summary": explanation.get("summary", ""),
        "what_it_does": explanation.get("what_it_does", ""),
        "when_to_use": explanation.get("when_to_use", []),
        "key_features": explanation.get("key_features", []),
        "example": explanation.get("example", ""),
        "raw_content": skill_content[:2000] if skill_content else "",
    }
    installed.append(skill_record)
    _save_installed(installed)

    logger.info(f"技能安装成功: {skill_name}")
    return skill_record


def _read_skill_md(skill_name: str) -> str:
    """尝试读取已安装技能的 SKILL.md 内容"""
    import glob

    # 常见的 skills 安装路径
    search_paths = [
        Path.home() / ".hermes" / "skills" / "**" / skill_name / "SKILL.md",
        Path.home() / ".hermes" / "skills" / "**" / f"{skill_name}.md",
        Path.home() / ".agents" / "skills" / "**" / skill_name / "SKILL.md",
    ]

    for pattern in search_paths:
        matches = glob.glob(str(pattern), recursive=True)
        if matches:
            try:
                with open(matches[0], "r", encoding="utf-8") as f:
                    return f.read()
            except Exception:
                pass

    return ""


async def _generate_explanation(skill_name: str, content: str) -> dict:
    """调用 LLM 生成技能的结构化说明"""
    if not content:
        return {
            "summary": f"{skill_name} 技能",
            "what_it_does": "暂无详细说明",
            "when_to_use": [],
            "key_features": [],
            "example": "",
        }

    prompt = f"""请根据以下技能文档，生成一份面向普通用户的结构化说明。
用简洁的中文回答，不要技术术语，让非程序员也能看懂。

技能名称: {skill_name}
技能文档:
---
{content[:3000]}
---

请用 JSON 格式回答:
{{
  "summary": "一句话说明这个技能是什么（20字以内）",
  "what_it_does": "详细说明这个技能能做什么（50-100字）",
  "when_to_use": ["使用场景1", "使用场景2", "使用场景3"],
  "key_features": ["核心功能1", "核心功能2", "核心功能3"],
  "example": "一个典型的使用示例（30字以内）"
}}"""

    try:
        response = await llm_service.call_llm(prompt)
        # 尝试解析 JSON
        import re
        json_match = re.search(r"\{[\s\S]*\}", response)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        logger.warning(f"AI 生成说明失败: {e}")

    return {
        "summary": f"{skill_name} 技能",
        "what_it_does": content[:100] if content else "暂无说明",
        "when_to_use": [],
        "key_features": [],
        "example": "",
    }


# ── 已安装管理 ──────────────────────────────────────────

def list_installed() -> list:
    """获取已安装技能列表"""
    return _load_installed()


def uninstall_skill(skill_name: str) -> bool:
    """卸载技能"""
    installed = _load_installed()
    before_count = len(installed)
    installed = [s for s in installed if s["name"] != skill_name]
    if len(installed) == before_count:
        return False
    _save_installed(installed)
    logger.info(f"技能已卸载: {skill_name}")
    return True


def get_skill_detail(skill_name: str) -> Optional[dict]:
    """获取单个已安装技能详情"""
    installed = _load_installed()
    for s in installed:
        if s["name"] == skill_name:
            return s
    return None
