# AI 交互流程详解

## 核心概念

### 提示词组装的三层结构

```
┌─────────────────────────────────────────────────────────────┐
│ 最终发送给 LLM 的完整 Prompt                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 第一层：System Prompt（系统提示词）                    │   │
│  │ 来源：.crew/system_rules.md + .crew/preferences.md  │   │
│  │ 作用：全局规则 + 用户个人偏好                         │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 第二层：Task Prompt（任务提示词）                     │   │
│  │ 来源：prompts/generator/*.prompt                     │   │
│  │ 作用：具体任务的指令和格式要求                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 完整流程图

### 1. 用户发起请求

```
用户请求：生成一个博客系统的 Crew
    ↓
API 接收：POST /api/ai-generator/generate
    ↓
调用：AIGeneratorService.generate_crew_from_scenario()
```

### 2. Topic 生成流程

```
AIGeneratorService.generate_topic()
    ↓
创建 AIClient 实例
    │
    ├─ 初始化 LLMFactory
    ├─ 初始化 DebugService
    └─ 从环境变量读取 debug 配置
    ↓
加载 Prompt 模板
    │
    └─ client.load_prompt("generator/topic.prompt", ...)
        │
        ├─ 读取文件：prompts/generator/topic.prompt
        ├─ 填充变量：scenario, context_section
        └─ 返回：Task Prompt
    ↓
调用 LLM
    │
    └─ client.call_structured(prompt, TopicResponse)
        │
        ├─ 加载 System Prompt
        │   │
        │   └─ preferences.load()
        │       │
        │       ├─ 读取：.crew/system_rules.md
        │       ├─ 读取：.crew/preferences.md
        │       └─ 拼接：system_rules + "\n\n" + preferences
        │
        ├─ 组装完整 Prompt
        │   │
        │   └─ full_prompt = system_prompt + "\n\n" + task_prompt
        │
        ├─ 调试日志（如果启用）
        │   │
        │   └─ debug.log_prompt(full_prompt, role="topic_generator")
        │
        ├─ 调用 LLM
        │   │
        │   └─ llm.invoke(full_prompt)
        │
        ├─ 调试日志（如果启用）
        │   │
        │   └─ debug.log_response(response, elapsed=1.23)
        │
        ├─ 提取 JSON
        │   │
        │   └─ extract_json(response)
        │
        └─ 解析为 Pydantic 模型
            │
            └─ TopicResponse.model_validate_json(json_str)
    ↓
返回：项目主题
```

### 3. Tasks 拆解流程

```
AIGeneratorService.generate_tasks()
    ↓
client.load_prompt("generator/tasks.prompt", ...)
    ↓
client.call_structured(prompt, TasksPlanResponse)
    │
    └─ 同样的流程：
        - 加载 System Prompt
        - 组装完整 Prompt
        - 调用 LLM
        - 解析响应
    ↓
返回：任务列表
```

### 4. Agent 匹配/创建流程

```
对于每个任务：
    ↓
AgentGenerator.match_or_create_agent()
    ↓
尝试匹配现有 Agent
    │
    └─ client.load_prompt("generator/agent_match.prompt", ...)
        └─ client.call_structured(prompt, AgentMatchResult)
    ↓
如果匹配失败，创建新 Agent
    │
    └─ client.load_prompt("generator/agent.prompt", ...)
        └─ client.call_structured(prompt, AgentConfig)
    ↓
AI 推荐 Skills（可选）
    │
    └─ skills_recommender.recommend_for_agent()
        │
        └─ client.load_prompt("generator/skills_recommendation.prompt", ...)
            └─ client.call_structured(prompt, SkillsRecommendationResponse)
    ↓
返回：Agent ID
```

### 5. 模型分配流程（待实现）

```
ModelAssigner.assign_models()
    ↓
client.load_prompt("generator/model_assignment.prompt", ...)
    ↓
client.call_structured(prompt, ModelAssignmentResponse)
    ↓
返回：每个 Agent 的模型等级
```

## 提示词组装详解

### System Prompt 的加载

```python
# 1. PreferencesLoader 初始化
preferences = PreferencesLoader()
preferences.project_root = /workspaces/one_person_company
preferences.system_rules_file = /workspaces/one_person_company/.crew/system_rules.md
preferences.preferences_file = /workspaces/one_person_company/.crew/preferences.md

# 2. 加载 System Prompt
system_prompt = preferences.load()

# 实际执行：
parts = []

# 读取 system_rules.md
if system_rules_file.exists():
    system_rules = system_rules_file.read_text()
    parts.append(system_rules)

# 读取 preferences.md
if preferences_file.exists():
    preferences_content = preferences_file.read_text()
    parts.append(preferences_content)

# 拼接
system_prompt = "\n\n".join(parts)
```

### Task Prompt 的加载

```python
# 1. 加载 prompt 模板
template = Path("prompts/generator/topic.prompt").read_text()

# 模板内容示例：
"""
# Role: 你是一名资深项目管理专家

## Task
根据以下场景，生成一个简洁的项目主题：

场景描述：{scenario}
{context_section}

## Output Format
返回 JSON 格式：
{{
  "topic": "项目主题"
}}
"""

# 2. 填充变量
task_prompt = template.format(
    scenario="开发一个博客系统",
    context_section="上下文：使用 FastAPI 和 Vue"
)

# 填充后：
"""
# Role: 你是一名资深项目管理专家

## Task
根据以下场景，生成一个简洁的项目主题：

场景描述：开发一个博客系统
上下文：使用 FastAPI 和 Vue

## Output Format
返回 JSON 格式：
{
  "topic": "项目主题"
}
"""
```

### 完整 Prompt 的组装

```python
# 最终发送给 LLM 的完整 Prompt
full_prompt = f"{system_prompt}\n\n{task_prompt}"

# 结构示例：
"""
# 系统规则（来自 .crew/system_rules.md）

你是一个 AI 助手，遵循以下规则：
1. 输出必须是有效的 JSON 格式
2. 使用中文回答
3. 保持简洁和专业

# 个人偏好（来自 .crew/preferences.md）

## 架构设计偏好
- 优先选择熟悉的技术栈
- 性能和可读性冲突时，优先可读性

## 输出风格偏好
- 文档结构要清晰，包含背景介绍
- 代码示例必须可运行

# Role: 你是一名资深项目管理专家

## Task
根据以下场景，生成一个简洁的项目主题：

场景描述：开发一个博客系统
上下文：使用 FastAPI 和 Vue

## Output Format
返回 JSON 格式：
{
  "topic": "项目主题"
}
"""
```

## 文件结构

```
/workspaces/one_person_company/
├── .crew/
│   ├── system_rules.md          # 系统规则（全局）
│   └── preferences.md            # 个人偏好（动态进化）
│
├── prompts/
│   ├── generator/
│   │   ├── topic.prompt          # Topic 生成
│   │   ├── tasks.prompt          # Tasks 拆解
│   │   ├── agent.prompt          # Agent 创建
│   │   ├── agent_match.prompt    # Agent 匹配
│   │   ├── skills_recommendation.prompt  # Skills 推荐
│   │   └── model_assignment.prompt       # 模型分配
│   │
│   └── preferences/
│       ├── evolution.prompt      # 偏好进化
│       └── diff_summary.prompt   # 变更摘要
│
└── .local/
    └── llm_debug/                # 调试日志（如果启用）
        ├── prompt_20260425-200530_123.txt
        └── response_20260425-200531_456.txt
```

## 代码路径

### 核心类

| 类 | 路径 | 职责 |
|---|------|------|
| `AIClient` | `crewai_web/core/ai/client.py` | LLM 交互客户端 |
| `PreferencesLoader` | `crewai_web/web/services/preferences_loader.py` | 加载 system_rules 和 preferences |
| `DebugService` | `crewai_web/core/debug_service.py` | 调试日志服务 |
| `LLMFactory` | `crewai_web/core/llm/factory.py` | LLM 实例工厂 |

### 服务类

| 服务 | 路径 | 职责 |
|------|------|------|
| `AIGeneratorService` | `crewai_web/web/services/ai_generator_service.py` | Crew 生成服务 |
| `AgentGenerator` | `crewai_web/web/services/agent_generator.py` | Agent 生成服务 |
| `TaskGenerator` | `crewai_web/web/services/task_generator.py` | Task 生成服务 |
| `SkillsRecommender` | `crewai_web/web/services/skills_recommender.py` | Skills 推荐服务 |

## 调用链示例

### 完整的 Topic 生成调用链

```
用户请求
    ↓
FastAPI Endpoint: /api/ai-generator/generate
    ↓
AIGeneratorService.generate_crew_from_scenario()
    ↓
AIGeneratorService.generate_topic()
    ↓
AIClient.__init__()
    ├─ LLMFactory.get_llm("default")
    │   ├─ DashScopeProvider.get_default_model()
    │   │   └─ LLMConfig.load()  # 从 JSON 读取默认模型
    │   └─ DashScopeProvider.create_llm(model)
    │
    └─ DebugService.__init__(debug_enabled=from_env)
    ↓
AIClient.load_prompt("generator/topic.prompt", ...)
    ├─ Path("prompts/generator/topic.prompt").read_text()
    └─ template.format(scenario=..., context_section=...)
    ↓
AIClient.call_structured(prompt, TopicResponse)
    ↓
PreferencesLoader.load()
    ├─ Path(".crew/system_rules.md").read_text()
    ├─ Path(".crew/preferences.md").read_text()
    └─ "\n\n".join([system_rules, preferences])
    ↓
full_prompt = system_prompt + "\n\n" + task_prompt
    ↓
DebugService.log_prompt(full_prompt)  # 如果启用
    ├─ logger.info(...)
    └─ Path(".local/llm_debug/prompt_xxx.txt").write_text(...)
    ↓
LLM.invoke(full_prompt)
    ├─ 调用 DashScope API
    └─ 返回响应文本
    ↓
DebugService.log_response(response)  # 如果启用
    ├─ logger.info(...)
    └─ Path(".local/llm_debug/response_xxx.txt").write_text(...)
    ↓
extract_json(response)
    └─ 提取 JSON 字符串
    ↓
TopicResponse.model_validate_json(json_str)
    └─ 解析为 Pydantic 模型
    ↓
返回：TopicResponse(topic="博客系统开发")
```

## 关键设计

### 1. 分层设计

```
┌─────────────────────────────────────┐
│ API Layer (FastAPI Endpoints)      │
├─────────────────────────────────────┤
│ Service Layer (Business Logic)     │
│ - AIGeneratorService                │
│ - AgentGenerator                    │
│ - TaskGenerator                     │
│ - SkillsRecommender                 │
├─────────────────────────────────────┤
│ Core Layer (Infrastructure)        │
│ - AIClient                          │
│ - PreferencesLoader                 │
│ - DebugService                      │
│ - LLMFactory                        │
└─────────────────────────────────────┘
```

### 2. 提示词管理

- ✅ **集中管理**：所有 prompt 文件在 `prompts/` 目录
- ✅ **模板化**：使用 Python `.format()` 填充变量
- ✅ **可复用**：同一个 prompt 可以被多个服务使用
- ✅ **易维护**：修改 prompt 不需要改代码

### 3. 偏好系统

- ✅ **全局规则**：`system_rules.md` 定义通用规则
- ✅ **个人偏好**：`preferences.md` 记录用户偏好
- ✅ **动态进化**：每次 Crew 执行后可以更新 preferences
- ✅ **缓存机制**：避免重复读取文件

### 4. 调试支持

- ✅ **环境变量控制**：`LLM_DEBUG_ENABLED=true`
- ✅ **双重输出**：日志 + 文件
- ✅ **Trace ID**：关联 prompt 和 response
- ✅ **角色标记**：区分不同 Agent 的调用

## 实际示例

### 示例 1：生成 Topic

**输入**：
```json
{
  "scenario": "开发一个博客系统",
  "context": "使用 FastAPI 和 Vue"
}
```

**Task Prompt**（来自 `prompts/generator/topic.prompt`）：
```markdown
# Role: 你是一名资深项目管理专家

## Task
根据以下场景，生成一个简洁的项目主题：

场景描述：开发一个博客系统
上下文：使用 FastAPI 和 Vue

## Output Format
返回 JSON 格式：
{
  "topic": "项目主题"
}
```

**System Prompt**（来自 `.crew/system_rules.md + preferences.md`）：
```markdown
# 系统规则
- 输出必须是有效的 JSON 格式
- 使用中文回答

# 个人偏好
- 优先选择熟悉的技术栈
```

**完整 Prompt**（发送给 LLM）：
```markdown
# 系统规则
- 输出必须是有效的 JSON 格式
- 使用中文回答

# 个人偏好
- 优先选择熟悉的技术栈

# Role: 你是一名资深项目管理专家

## Task
根据以下场景，生成一个简洁的项目主题：

场景描述：开发一个博客系统
上下文：使用 FastAPI 和 Vue

## Output Format
返回 JSON 格式：
{
  "topic": "项目主题"
}
```

**LLM 响应**：
```json
{
  "topic": "FastAPI + Vue 博客系统开发"
}
```

**解析结果**：
```python
TopicResponse(topic="FastAPI + Vue 博客系统开发")
```

### 示例 2：推荐 Skills

**输入**：
```json
{
  "role": "前端工程师",
  "goal": "开发高质量的前端代码",
  "backstory": "我是一位资深前端工程师",
  "task_context": "开发电商网站"
}
```

**Task Prompt**（来自 `prompts/generator/skills_recommendation.prompt`）：
```markdown
# Role
你是一个 AI Agent Skills 推荐专家

# Task
为以下 Agent 推荐最合适的 Skills：

**Agent 信息**：
- 角色：前端工程师
- 目标：开发高质量的前端代码
- 背景：我是一位资深前端工程师
- 任务上下文：开发电商网站

**可用的 Skills**：
- frontend-tools: 前端开发工具和规范
- backend-tools: 后端开发工具和规范
- code-review: 代码审查工具

# Output Format
返回 JSON 格式：
{
  "recommended_skills": [...]
}
```

**完整 Prompt** = System Prompt + Task Prompt

**LLM 响应**：
```json
{
  "recommended_skills": [
    {
      "skill_name": "frontend-tools",
      "reason": "前端工程师必备的工具和规范",
      "priority": "high"
    }
  ],
  "mode": "hybrid"
}
```

## 总结

### 提示词组装流程

1. **加载 System Prompt**
   - 读取 `.crew/system_rules.md`（全局规则）
   - 读取 `.crew/preferences.md`（用户偏好）
   - 拼接为 System Prompt

2. **加载 Task Prompt**
   - 读取 `prompts/generator/*.prompt`（任务模板）
   - 填充变量（scenario, role, goal 等）
   - 生成 Task Prompt

3. **组装完整 Prompt**
   - `full_prompt = system_prompt + "\n\n" + task_prompt`

4. **调用 LLM**
   - 发送 full_prompt 到 LLM
   - 接收响应
   - 解析为 Pydantic 模型

5. **调试日志**（如果启用）
   - 记录 prompt 到日志和文件
   - 记录 response 到日志和文件

### 关键优势

- ✅ **灵活性**：System Prompt 和 Task Prompt 分离
- ✅ **可维护性**：Prompt 文件化，易于修改
- ✅ **可扩展性**：新增任务只需添加新的 prompt 文件
- ✅ **可调试性**：完整的日志和文件记录
- ✅ **个性化**：支持用户偏好的动态进化

---

**更新时间**: 2026-04-26  
**核心理念**: 分层设计，提示词模板化，偏好动态进化
