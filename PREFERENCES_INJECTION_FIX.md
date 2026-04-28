# 偏好注入问题修复

## 问题发现

用户发现调用 `http://localhost:5173/api/skills/ai-recommend` 时，LLM 收到的 prompt 中包含了系统规则和偏好，但 Skills 推荐是**系统内置 AI 交互**，不应该注入偏好。

### 问题代码

`@/workspaces/one_person_company/crewai_web/web/services/skills_recommender.py:83-88`

```python
# ❌ 错误：Skills 推荐不应该注入偏好
recommendation = await self.ai_client.call_structured(
    prompt=prompt,
    response_model=SkillsRecommendationResponse,
    role=role,
    inject_preferences=True  # ❌ 错误！
)
```

### 问题影响

**修复前的 prompt**（包含偏好规则）：
```markdown
# 系统规则（来自 .crew/system_rules.md）
- 输出必须是有效的 JSON 格式
- 使用中文回答

# 个人偏好（来自 .crew/preferences.md）
- 优先选择熟悉的技术栈
- 性能和可读性冲突时，优先可读性

# Role
你是一个 AI Agent Skills 推荐专家

# Task
为以下 Agent 推荐最合适的 Skills：
...
```

**修复后的 prompt**（纯净的任务 prompt）：
```markdown
# Role
你是一个 AI Agent Skills 推荐专家

# Task
为以下 Agent 推荐最合适的 Skills：
...
```

## 修复方案

### 1. 移除错误的偏好注入

`@/workspaces/one_person_company/crewai_web/web/services/skills_recommender.py:83-88`

```python
# ✅ 正确：使用默认值 inject_preferences=False
recommendation = await self.ai_client.call_structured(
    prompt=prompt,
    response_model=SkillsRecommendationResponse,
    role=role
    # inject_preferences=False  # 默认值，系统内置 AI 交互不注入偏好
)
```

### 2. 检查所有服务

检查结果：

| 服务 | 方法 | `inject_preferences` | 状态 |
|------|------|---------------------|------|
| `AIGeneratorService` | `generate_topic()` | 未设置（默认 False） | ✅ 正确 |
| `AIGeneratorService` | `generate_tasks()` | 未设置（默认 False） | ✅ 正确 |
| `AgentGenerator` | `match_agent()` | 未设置（默认 False） | ✅ 正确 |
| `AgentGenerator` | `create_agent()` | 未设置（默认 False） | ✅ 正确 |
| `SkillsRecommender` | `recommend_for_agent()` | ~~True~~ → False | ✅ 已修复 |
| `PreferencesEvolutionService` | `generate_evolution()` | 显式 False | ✅ 正确 |
| `PreferencesEvolutionService` | `generate_diff_summary()` | 显式 False | ✅ 正确 |

## 设计原则

### 系统内置 AI 交互（不注入偏好）

这些操作是系统内部的，prompt 已经包含了完整的指令，不需要用户偏好：

```python
# ✅ Topic 生成
prompt = client.load_prompt("generator/topic.prompt", ...)
response = await client.call_structured(prompt, TopicResponse)
# inject_preferences=False（默认）

# ✅ Tasks 拆解
prompt = client.load_prompt("generator/tasks.prompt", ...)
response = await client.call_structured(prompt, TasksPlanResponse)
# inject_preferences=False（默认）

# ✅ Agent 创建
prompt = client.load_prompt("generator/agent.prompt", ...)
response = await client.call_structured(prompt, AgentConfig)
# inject_preferences=False（默认）

# ✅ Skills 推荐
prompt = client.load_prompt("generator/skills_recommendation.prompt", ...)
response = await client.call_structured(prompt, SkillsRecommendationResponse)
# inject_preferences=False（默认）

# ✅ 偏好进化
prompt = builder.build_evolution_prompt(...)
response = await client.call(prompt, inject_preferences=False)
# 显式设置为 False
```

### Crew 动态编排（注入偏好）

只有在 Agent 执行用户的实际任务时，才需要注入偏好：

```python
# ✅ Agent 执行任务（未来实现）
task_prompt = f"""
你是 {agent.role}，你的目标是：{agent.goal}

请完成以下任务：
{task.description}
"""

response = await client.call_text(
    prompt=task_prompt,
    inject_preferences=True  # ✅ 显式启用
)
```

## 为什么 Skills 推荐不需要偏好？

### 1. 职责分离

- **Skills 推荐**：系统根据 Agent 的角色和目标，推荐合适的工具
- **用户偏好**：用户在执行任务时的个人风格和习惯

这两者是独立的：
- Skills 推荐关注"这个 Agent 需要什么工具"
- 用户偏好关注"用户喜欢怎样的输出风格"

### 2. Prompt 已经完整

`prompts/generator/skills_recommendation.prompt` 已经包含了：
- 角色定义
- 任务描述
- 推荐规则
- 输出格式
- 示例

不需要额外的偏好规则。

### 3. 避免干扰

如果注入偏好，可能会干扰 Skills 推荐的逻辑：

```markdown
# 个人偏好（不相关）
- 优先选择熟悉的技术栈
- 性能和可读性冲突时，优先可读性

# Skills 推荐任务（相关）
为前端工程师推荐 Skills
```

偏好规则是关于"技术选型"和"代码风格"的，与 Skills 推荐无关。

## 测试验证

### 修复前

```bash
# 调用 Skills 推荐 API
curl -X POST http://localhost:8000/api/skills/ai-recommend \
  -d '{"role": "前端工程师", "goal": "开发前端代码"}'

# 查看调试日志
cat .local/llm_debug/prompt_*.txt | tail -1
```

**Prompt 内容**（包含偏好）：
```markdown
# 系统规则
...

# 个人偏好
...

# Role
你是一个 AI Agent Skills 推荐专家
...
```

### 修复后

```bash
# 重启后端
# 调用 Skills 推荐 API
curl -X POST http://localhost:8000/api/skills/ai-recommend \
  -d '{"role": "前端工程师", "goal": "开发前端代码"}'

# 查看调试日志
cat .local/llm_debug/prompt_*.txt | tail -1
```

**Prompt 内容**（纯净）：
```markdown
# Role
你是一个 AI Agent Skills 推荐专家

# Task
为以下 Agent 推荐最合适的 Skills：
...
```

## 总结

### 修复内容

1. ✅ 移除 `SkillsRecommender` 中的 `inject_preferences=True`
2. ✅ 验证其他服务都使用默认值 `inject_preferences=False`
3. ✅ 确保只有 Crew 执行时才注入偏好

### 设计原则

| 场景 | 注入偏好 | 原因 |
|------|---------|------|
| 系统内置 AI 交互 | ❌ 否 | Prompt 已完整，不需要偏好 |
| Crew 动态编排 | ✅ 是 | Agent 执行任务，需要偏好 |

### 核心理念

- **默认不注入**：系统内置操作保持 prompt 纯净
- **显式启用**：只在 Crew 执行时明确需要偏好
- **职责分离**：系统操作和用户任务分离

---

**修复时间**: 2026-04-26  
**问题**: Skills 推荐错误地注入了偏好规则  
**解决**: 移除 `inject_preferences=True`，使用默认值 `False`
