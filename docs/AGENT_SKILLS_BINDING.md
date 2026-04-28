# Agent 与 Skills 绑定机制

## 概述

本文档说明如何配置 Agent 使用特定的 Skills，支持三种模式：
- **auto**: 自动匹配所有相关 Skills（默认）
- **manual**: 只使用手动指定的 Skills
- **hybrid**: 优先使用指定 Skills，同时自动匹配其他相关 Skills

---

## 配置格式

### Agent 配置示例

```json
{
  "name": "python_developer",
  "role": "Python 开发工程师",
  "goal": "编写高质量的 Python 代码",
  "backstory": "...",
  "skills_config": {
    "mode": "hybrid",
    "preferred": ["code-generator"],
    "auto_match": true,
    "include_patterns": ["python-*", "code-*"],
    "exclude_patterns": ["java-*", "go-*"]
  }
}
```

### 字段说明

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `mode` | string | `"auto"` | 模式：`auto` / `manual` / `hybrid` |
| `preferred` | string[] | `[]` | 优先使用的 Skills 名称列表 |
| `auto_match` | boolean | `true` | 是否自动匹配相关 Skills |
| `include_patterns` | string[] | `[]` | 包含的 Skills 模式（支持通配符） |
| `exclude_patterns` | string[] | `[]` | 排除的 Skills 模式（支持通配符） |

---

## 三种模式详解

### 1. Auto 模式（默认）

**特点**：自动加载所有相关 Skills，无需手动配置

```json
{
  "skills_config": {
    "mode": "auto"
  }
}
```

或者完全不配置 `skills_config`（默认行为）。

**适用场景**：
- 通用 Agent
- 不确定需要哪些 Skills
- 希望 Agent 拥有最大能力

---

### 2. Manual 模式

**特点**：只使用手动指定的 Skills，不自动匹配

```json
{
  "skills_config": {
    "mode": "manual",
    "preferred": ["code-generator", "python-linter"]
  }
}
```

**适用场景**：
- 专业化 Agent（如"代码审查专家"只需要审查相关 Skills）
- 需要精确控制 Agent 能力
- 避免 Skills 冲突

---

### 3. Hybrid 模式（推荐）

**特点**：优先使用指定 Skills，同时自动匹配其他相关 Skills

```json
{
  "skills_config": {
    "mode": "hybrid",
    "preferred": ["code-generator"],
    "auto_match": true,
    "include_patterns": ["python-*"],
    "exclude_patterns": ["java-*"]
  }
}
```

**工作流程**：
1. 首先加载 `preferred` 中的 Skills
2. 然后自动匹配符合 `include_patterns` 的 Skills
3. 排除符合 `exclude_patterns` 的 Skills

**适用场景**：
- 大多数场景（推荐）
- 既需要特定 Skills，又希望有一定灵活性
- 需要排除不相关的 Skills

---

## 通配符模式

支持 Unix shell 风格的通配符：

| 模式 | 说明 | 示例 |
|------|------|------|
| `*` | 匹配任意字符 | `python-*` 匹配 `python-linter`, `python-formatter` |
| `?` | 匹配单个字符 | `code-?` 匹配 `code-a`, `code-b` |
| `[abc]` | 匹配括号中的任一字符 | `code-[abc]` 匹配 `code-a`, `code-b`, `code-c` |
| `[!abc]` | 匹配不在括号中的字符 | `code-[!abc]` 不匹配 `code-a` |

### 示例

```json
{
  "include_patterns": [
    "python-*",      // 所有 Python 相关
    "*-generator",   // 所有生成器
    "code-*"         // 所有代码相关
  ],
  "exclude_patterns": [
    "java-*",        // 排除所有 Java 相关
    "*-deprecated"   // 排除所有已废弃的
  ]
}
```

---

## 实际案例

### 案例 1: Python 开发工程师

```json
{
  "name": "python_developer",
  "role": "Python 开发工程师",
  "skills_config": {
    "mode": "hybrid",
    "preferred": ["code-generator"],
    "include_patterns": ["python-*", "code-*"],
    "exclude_patterns": ["java-*", "go-*", "rust-*"]
  }
}
```

**结果**：
- ✅ 优先使用 `code-generator`
- ✅ 自动加载 `python-linter`, `python-formatter`
- ✅ 自动加载 `code-reviewer`
- ❌ 排除 `java-generator`, `go-linter`

---

### 案例 2: 代码审查专家

```json
{
  "name": "code_reviewer",
  "role": "代码审查专家",
  "skills_config": {
    "mode": "manual",
    "preferred": ["code-reviewer", "security-checker"]
  }
}
```

**结果**：
- ✅ 只使用 `code-reviewer` 和 `security-checker`
- ❌ 不加载其他任何 Skills

---

### 案例 3: 全栈工程师

```json
{
  "name": "fullstack_developer",
  "role": "全栈工程师",
  "skills_config": {
    "mode": "auto"
  }
}
```

**结果**：
- ✅ 加载所有可用的 Skills
- 最大化 Agent 能力

---

## API 使用

### 创建 Agent 时指定 Skills 配置

```python
from crewai_web.web.domain.agent import AgentCreate, SkillsConfig

agent = AgentCreate(
    name="python_dev",
    role="Python 开发工程师",
    goal="编写高质量代码",
    backstory="...",
    skills_config=SkillsConfig(
        mode="hybrid",
        preferred=["code-generator"],
        include_patterns=["python-*"],
        exclude_patterns=["java-*"]
    )
)
```

### 更新 Agent 的 Skills 配置

```python
from crewai_web.web.domain.agent import AgentUpdate, SkillsConfig

update = AgentUpdate(
    skills_config=SkillsConfig(
        mode="manual",
        preferred=["code-generator", "python-linter"]
    )
)

# 通过 API 更新
api.agents.update(agent_id, update)
```

---

## 前端配置

在前端 Agent 表单中添加 Skills 配置：

```vue
<el-form-item label="Skills 模式">
  <el-select v-model="form.skills_config.mode">
    <el-option label="自动匹配" value="auto" />
    <el-option label="手动指定" value="manual" />
    <el-option label="混合模式" value="hybrid" />
  </el-select>
</el-form-item>

<el-form-item label="优先 Skills">
  <el-select
    v-model="form.skills_config.preferred"
    multiple
    filterable
  >
    <el-option
      v-for="skill in availableSkills"
      :key="skill.name"
      :label="skill.name"
      :value="skill.name"
    />
  </el-select>
</el-form-item>
```

---

## 调试和验证

### 查看 Agent 实际加载的 Skills

```python
from crewai_web.core.tools import get_loader
from crewai_web.web.services.agent_service import get_agent

agent = get_agent("python_dev")
loader = get_loader()

skills_config = agent.skills_config.model_dump() if agent.skills_config else None
skills = loader.get_skills_for_agent(agent.role, skills_config)

print(f"Agent {agent.name} 加载的 Skills:")
for skill in skills:
    print(f"  - {Path(skill).parent.name}")
```

### 日志输出

启用调试日志查看 Skills 加载过程：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 最佳实践

### 1. 优先使用 Hybrid 模式

```json
{
  "mode": "hybrid",
  "preferred": ["核心 Skill"],
  "include_patterns": ["相关模式"],
  "exclude_patterns": ["不相关模式"]
}
```

### 2. 明确排除不相关 Skills

```json
{
  "exclude_patterns": ["java-*", "go-*"]  // Python Agent 排除其他语言
}
```

### 3. 为专业 Agent 使用 Manual 模式

```json
{
  "mode": "manual",
  "preferred": ["specific-skill"]  // 代码审查专家只需要审查 Skill
}
```

### 4. 定期审查 Agent 的 Skills 配置

- 检查是否有不必要的 Skills
- 确认是否缺少关键 Skills
- 根据实际使用情况调整

---

## 故障排查

### Q: Agent 没有加载预期的 Skills？

**A**: 检查以下几点：
1. Skills 名称是否正确（区分大小写）
2. `exclude_patterns` 是否意外排除了该 Skill
3. `mode` 是否设置为 `manual` 但未在 `preferred` 中指定

### Q: Agent 加载了不需要的 Skills？

**A**: 
1. 使用 `exclude_patterns` 排除
2. 或改用 `manual` 模式精确控制

### Q: 通配符不生效？

**A**: 
- 确保使用正确的通配符语法（`*`, `?`, `[]`）
- 检查是否有拼写错误

---

## 未来规划

### 短期
- [ ] 前端 UI 支持 Skills 配置
- [ ] Skills 使用统计和推荐

### 中期
- [ ] 基于 embedding 的智能 Skills 匹配
- [ ] Skills 冲突检测和解决

### 长期
- [ ] Agent 自动学习最优 Skills 组合
- [ ] Skills 版本管理和兼容性检查

---

**最后更新**: 2026-04-17
