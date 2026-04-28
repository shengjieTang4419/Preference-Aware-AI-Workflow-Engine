# 项目偏好文件使用指南

## 概述

项目偏好文件 (`.crew/preferences.md`) 是一个 Markdown 文件，定义了 AI Agent 在项目中的工作规范、编码风格、技术栈偏好等。

**核心理念：一次定义，全局生效**
- 所有 AI 生成的代码都会遵循这些规范
- 根据 Agent 角色自动注入相关偏好
- 类似 Claude Code 的 `CLAUDE.md`，但更灵活

---

## 文件位置

```
/workspaces/one_person_company/
└── .crew/
    └── preferences.md  # 项目偏好文件
```

---

## 文件格式

### 基本结构

```markdown
# 项目偏好设置

本文件定义了 AI Agent 在此项目中的工作偏好和规范。

---

## 编码规范

### Python
- **风格**: 遵循 PEP 8
- **类型注解**: 所有函数必须有类型注解
...

## 技术栈偏好

### 后端
- **框架**: FastAPI
...

## 安全规范

### 敏感信息
- **禁止**: 硬编码 API Key
...

---

**最后更新**: 2026-04-17
**维护者**: 团队名称
```

### 章节组织

推荐的章节结构：

1. **编码规范** — 语言特定的代码风格
2. **技术栈偏好** — 框架、库的选择
3. **项目结构约定** — 目录组织、命名规范
4. **AI 生成代码规范** — AI 特定的要求
5. **安全规范** — 安全最佳实践
6. **注释和文档** — 文档字符串规范
7. **Git 提交规范** — Commit message 格式
8. **测试规范** — 测试覆盖率要求
9. **日志规范** — 日志级别和格式
10. **性能目标** — 响应时间等指标

---

## 工作原理

### 自动注入流程

```
用户请求
    ↓
AIClient.call() / call_structured()
    ↓
加载 preferences.md
    ↓
根据 Agent 角色提取相关章节
    ↓
合并到 system prompt
    ↓
发送给 LLM
    ↓
生成符合规范的代码
```

### 角色匹配逻辑

系统会根据 Agent 角色关键词自动选择相关章节：

| 角色关键词 | 自动注入的章节 |
|-----------|--------------|
| `python` | 编码规范、技术栈偏好、AI 生成代码规范、安全规范 |
| `java` | 编码规范、AI 生成代码规范、安全规范 |
| `javascript` / `typescript` | 编码规范、技术栈偏好、AI 生成代码规范 |
| `前端` | 编码规范、技术栈偏好 |
| `后端` | 编码规范、技术栈偏好、安全规范 |
| `产品` | 项目结构约定、Git 提交规范 |
| `测试` | 测试规范、代码审查清单 |
| **其他** | 编码规范、AI 生成代码规范、安全规范（默认） |

---

## 使用方式

### 1. 自动注入（推荐）

**所有 AI 调用默认自动注入偏好**，无需手动操作：

```python
# 在 agent_generator.py 中
agent_config = await self.ai_client.call_structured(
    prompt=prompt,
    response_model=AgentConfig,
    role="Python 开发工程师"  # ← 自动注入 Python 相关偏好
)
```

### 2. 手动加载（高级用法）

```python
from crewai_web.core.preferences import get_preferences

# 获取加载器
loader = get_preferences()

# 加载完整偏好
full_content = loader.load()

# 获取特定章节
coding_standards = loader.get_section("编码规范")

# 根据角色获取相关偏好
python_prefs = loader.get_for_role("Python 开发工程师")

# 生成 system prompt
system_prompt = loader.get_system_prompt(
    role="Python 开发工程师",
    context="你正在生成一个 FastAPI 服务"
)
```

### 3. 禁用自动注入（特殊场景）

```python
# 某些场景下可能不需要偏好（如纯文本生成）
response = await ai_client.call(
    prompt="生成一个产品介绍",
    inject_preferences=False  # ← 禁用偏好注入
)
```

---

## 最佳实践

### 1. 保持简洁明了

❌ **不好**：
```markdown
## 编码规范

在编写 Python 代码时，我们需要遵循 PEP 8 规范，这是 Python 官方推荐的代码风格指南。
具体来说，我们需要注意以下几点：首先，缩进使用 4 个空格...（长篇大论）
```

✅ **好**：
```markdown
## 编码规范

### Python
- **风格**: PEP 8，使用 Black 格式化
- **类型注解**: 必须
- **文档字符串**: Google 风格
```

### 2. 使用示例代码

```markdown
### 错误处理

所有外部调用必须有 try-except：

```python
try:
    result = await api_call()
except APIError as e:
    logger.error(f"API 调用失败: {e}")
    raise
```
```

### 3. 分层组织

```markdown
## 编码规范

### Python
（Python 特定规范）

### JavaScript/TypeScript
（JS/TS 特定规范）

### 通用规范
（所有语言共享的规范）
```

### 4. 定期更新

在文件底部记录更新信息：

```markdown
---

**最后更新**: 2026-04-17
**维护者**: 开发团队
**版本**: 1.2
```

---

## 常见场景

### 场景 1: 新项目初始化

```markdown
## 技术栈偏好

### 后端
- **框架**: FastAPI
- **数据库**: PostgreSQL
- **ORM**: SQLAlchemy

### 前端
- **框架**: React + TypeScript
- **UI 库**: Material-UI
```

### 场景 2: 多语言项目

```markdown
## 编码规范

### Python
- PEP 8 + Black

### Java
- Google Java Style Guide

### Go
- gofmt + golangci-lint
```

### 场景 3: 安全敏感项目

```markdown
## 安全规范

### 强制要求
- [ ] 所有 API 必须有认证
- [ ] 所有输入必须验证
- [ ] 敏感数据必须加密
- [ ] 定期安全审计

### 禁止事项
- ❌ 硬编码密钥
- ❌ 使用弱加密算法
- ❌ 信任用户输入
```

---

## 测试你的偏好文件

```bash
# 运行测试脚本
uv run python test_preferences.py
```

输出示例：
```
📚 测试 1: 加载完整偏好文件
✅ 成功加载: 3766 字符

📖 测试 2: 获取特定章节
✅ 编码规范: 492 字符
✅ 技术栈偏好: 143 字符

👤 测试 3: 根据角色获取相关偏好
角色: Python 开发工程师
  包含章节: 技术栈偏好, 编码规范, AI 生成代码规范, 安全规范
```

---

## 故障排查

### Q: 偏好没有生效？

**A**: 检查以下几点：
1. 文件路径是否正确：`.crew/preferences.md`
2. 文件格式是否正确（Markdown + 二级标题）
3. 查看日志确认是否加载成功

### Q: 如何验证 AI 是否使用了偏好？

**A**: 查看生成的代码是否符合规范：
- Python 代码是否有类型注解
- 是否使用了指定的框架
- 错误处理是否完善

### Q: 偏好文件太大会影响性能吗？

**A**: 
- 系统会根据角色只提取相关章节
- 建议单个章节不超过 500 字
- 总文件大小建议 < 10KB

### Q: 如何为不同环境设置不同偏好？

**A**: 可以创建多个偏好文件：
```
.crew/
├── preferences.md          # 默认
├── preferences.dev.md      # 开发环境
└── preferences.prod.md     # 生产环境
```

然后在代码中动态选择：
```python
env = os.getenv("ENV", "default")
loader = PreferencesLoader(
    preferences_file=f".crew/preferences.{env}.md"
)
```

---

## 高级功能（计划中）

### 偏好继承

```markdown
---
extends: .crew/base-preferences.md
---

# 项目特定偏好
（覆盖或扩展基础偏好）
```

### 条件偏好

```markdown
## 编码规范

### Python

{% if project.type == "web" %}
- 使用 FastAPI
{% elif project.type == "cli" %}
- 使用 Click
{% endif %}
```

### 偏好验证

```bash
# 验证偏好文件格式
uv run python -m crewai_web.core.preferences validate
```

---

## 参考资源

- [Claude Code CLAUDE.md 文档](https://code.claude.com/docs/en/memory)
- [Google Style Guides](https://google.github.io/styleguide/)
- [PEP 8 — Python 代码风格指南](https://peps.python.org/pep-0008/)

---

## 贡献偏好模板

欢迎分享你的偏好文件模板！

**提交方式**：
1. Fork 本项目
2. 在 `templates/preferences/` 目录下创建模板
3. 提交 Pull Request

**模板命名**：
- `python-web.md` — Python Web 项目
- `java-spring.md` — Java Spring 项目
- `react-ts.md` — React + TypeScript 项目
