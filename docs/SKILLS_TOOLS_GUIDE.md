# Skills & Tools 使用指南

## 概述

本项目支持从 **Claude Skills** 目录直接加载 Skills 和 Tools，无需手动转换。

**核心理念：统一格式，自动识别**
- **Skills**（知识/指导）→ Markdown 文件 → 注入到 Agent prompt
- **Tools**（可执行能力）→ Python 脚本 → 包装为 CrewAI Tools

---

## 目录结构

### 1. 挂载你的 Claude Skills（推荐）

```bash
# macOS/Linux 本地路径
~/.claude/skills/
├── code-review/
│   ├── SKILL.md          # 代码审查规范（自动加载为 Skill）
│   └── scripts/
│       └── lint.py       # 代码检查脚本（自动包装为 Tool）
├── api-design/
│   └── SKILL.md          # API 设计原则
└── ...
```

**容器内自动挂载到**: `/workspace/external_skills/`

### 2. 项目内置 Skills

```bash
/workspaces/one_person_company/skills/
├── code-generator/
│   ├── SKILL.md          # 代码生成规范
│   └── scripts/
│       └── write_file.py # 文件写入工具
└── ...
```

---

## Skills 格式（Markdown + YAML Frontmatter）

### 示例：`SKILL.md`

```markdown
---
name: code-review
description: 代码审查指南，关注安全性和性能
metadata:
  author: your-team
  version: "1.0"
---

## 代码审查清单

当审查代码时，检查以下方面：

1. **安全性**: 注入漏洞、认证绕过、数据泄露
2. **性能**: N+1 查询、不必要的内存分配
3. **可读性**: 清晰的命名、适当的注释
4. **测试**: 新功能的测试覆盖率

### 严重性级别
- **Critical**: 安全漏洞 → 阻止合并
- **Major**: 性能问题 → 要求修改
- **Minor**: 代码风格 → 批准并评论
```

**这个格式与 Claude Skills 完全兼容！** 无需任何转换。

---

## Tools 格式（Python 脚本）

### 脚本规范

在 `scripts/` 目录下创建 `.py` 文件，必须包含：

1. **`run(input: str) -> str` 函数**（必需）
2. **`TOOL_NAME`** 常量（可选，默认为文件名）
3. **`TOOL_DESCRIPTION`** 常量（可选）

### 示例：`scripts/write_file.py`

```python
"""文件写入工具"""
import json
from pathlib import Path

# Tool 元数据
TOOL_NAME = "write_code_file"
TOOL_DESCRIPTION = "将生成的代码写入到指定文件路径"


def run(input: str) -> str:
    """
    执行文件写入
    
    Args:
        input: JSON 字符串，格式: {"file_path": "路径", "content": "内容"}
    
    Returns:
        执行结果描述
    """
    try:
        data = json.loads(input)
        file_path = data["file_path"]
        content = data["content"]
        
        # 写入逻辑
        Path(file_path).write_text(content, encoding="utf-8")
        
        return f"✅ 文件已写入: {file_path}"
    except Exception as e:
        return f"❌ 错误: {e}"
```

---

## 使用方式

### 自动加载（推荐）

Agent 创建时会**自动加载所有 Skills 和 Tools**：

```python
# crewai_web/web/runner/dynamic_crew_builder.py

def _create_agent(self, agent_config, inputs=None):
    # 自动加载 Skills 和 Tools
    loader = get_loader()
    skills = loader.get_skills_for_agent(role)  # 所有 SKILL.md
    tools = loader.get_tools_for_agent(role)    # 所有 scripts/*.py
    
    return Agent(
        role=role,
        skills=skills,  # ← 自动注入
        tools=tools,    # ← 自动注入
        ...
    )
```

### 手动加载（高级用法）

```python
from crewai_web.core.tools import get_loader

loader = get_loader()
skills, tools = loader.load_all()

print(f"加载了 {len(skills)} 个 Skills")
print(f"加载了 {len(tools)} 个 Tools")
```

---

## 测试你的 Skills/Tools

```bash
# 运行测试脚本
uv run python test_skills_loader.py
```

输出示例：
```
📚 加载的 Skills (1 个):
  ✅ /workspaces/.../skills/code-generator/SKILL.md

🔧 加载的 Tools (1 个):
  ✅ write_code_file: 将生成的代码写入到指定文件路径

🧪 测试第一个 Tool: write_code_file
  结果: ✅ 文件已写入: /tmp/crew_output/test.txt (21 字符)
```

---

## 最佳实践

### 1. Skills（知识型）适用场景
- 编码规范（如 PEP 8、Google Style Guide）
- 设计模式和架构原则
- 领域知识（如金融术语、医疗流程）
- 项目特定的约定

### 2. Tools（执行型）适用场景
- 文件读写操作
- API 调用（GitHub、Jira、数据库等）
- 代码执行和测试
- 数据处理和转换

### 3. 命名规范
- **Skill 目录**: 小写字母 + 连字符（如 `code-review`）
- **Tool 脚本**: 动词开头（如 `write_file.py`、`run_tests.py`）
- **Tool 名称**: 清晰描述功能（如 `write_code_file`）

### 4. 安全注意事项
- ⚠️ **永远不要**在 Skills/Tools 中硬编码敏感信息
- ✅ 使用环境变量或配置文件
- ✅ 验证所有外部输入
- ✅ 限制文件操作的目录范围

---

## 高级功能（TODO）

### 智能匹配（计划中）
根据 Agent 角色自动选择相关的 Skills/Tools：

```python
# 未来功能
loader.get_skills_for_agent("Java 开发工程师")
# → 只返回 Java 相关的 Skills

loader.get_tools_for_agent("前端开发")
# → 只返回前端相关的 Tools（npm、webpack 等）
```

### Skills 版本管理（计划中）
支持多版本 Skills 共存：

```markdown
---
name: code-review
version: "2.0"
deprecated: false
---
```

---

## 故障排查

### Q: Skills 没有被加载？
**A**: 检查目录结构：
```bash
ls -la /workspace/external_skills  # 挂载的 Claude skills
ls -la /workspaces/one_person_company/skills  # 项目内置
```

### Q: Tool 执行报错？
**A**: 确保脚本有 `run(input: str) -> str` 函数：
```python
def run(input: str) -> str:
    return "result"
```

### Q: 如何调试 Tool？
**A**: 直接运行脚本：
```bash
cd skills/your-skill/scripts
python your_tool.py
```

---

## 贡献你的 Skills/Tools

欢迎分享你的 Skills 和 Tools！

1. Fork 本项目
2. 在 `skills/` 目录下创建新的 skill
3. 提交 Pull Request

**格式要求**：
- Skills: 必须有 `SKILL.md`
- Tools: 必须有 `run(input: str) -> str` 函数
- 添加使用示例和说明

---

## 参考资源

- [Claude Skills 官方文档](https://code.claude.com/docs/en/skills)
- [CrewAI Tools 文档](https://docs.crewai.com/en/concepts/tools)
- [CrewAI Skills 文档](https://docs.crewai.com/en/concepts/skills)
