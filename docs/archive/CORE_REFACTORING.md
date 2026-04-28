# Core 层重构文档

## 重构目标

1. **分层清晰** - AI 交互层、服务层、工具层分离
2. **职责单一** - 每个模块只做一件事
3. **符合 DESIGN.md** - Preferences 只负责加载文件，不包含进化逻辑

---

## 新的目录结构

```
crewai_web/
├── core/                    # 纯技术组件层
│   ├── ai/                 # AI 交互层
│   │   ├── __init__.py
│   │   ├── client.py       # AIClient - LLM 调用客户端
│   │   ├── protocol.py     # 协议定义（PromptToText, PromptToModel）
│   │   └── prompt_loader.py # Prompt 模板加载器
│   │
│   ├── llm/                # LLM 提供商管理
│   │   ├── __init__.py
│   │   ├── base_provider.py
│   │   ├── dashscope_provider.py
│   │   ├── claude_provider.py
│   │   └── factory.py
│   │
│   ├── tools/              # 纯工具封装
│   │   └── skills/         # Skills 管理
│   │
│   ├── chain/              # 编排层
│   │   └── ...
│   │
│   ├── debug_service.py    # 调试服务
│   ├── json_utils.py       # JSON 工具
│   └── alerters.py         # 告警服务
│
└── web/                     # 业务层
    ├── services/            # 业务服务
    │   ├── preferences_loader.py  # 偏好加载（业务逻辑）
    │   ├── preferences_evolution_service.py
    │   └── ...
    │
    └── api/                 # API 路由
        └── ...
```

---

## 核心模块职责

### 1. AI 交互层 (`core/ai/`)

**职责：**
- LLM 调用封装
- Prompt 管理
- 协议定义

**模块：**

#### `client.py` - AIClient
```python
from crewai_web.core.ai import AIClient

client = AIClient(llm_key="default")
result = await client.call(prompt, ResponseModel)
text = await client.call_text(prompt)
```

- 集成 LLM Factory
- 自动加载 Preferences
- 集成调试服务
- 支持重试机制

#### `protocol.py` - 协议定义
```python
from crewai_web.core.ai import PromptToText, PromptToModel

# 定义标准接口
```

#### `prompt_loader.py` - Prompt 模板加载
```python
from crewai_web.core.ai import PromptLoader

loader = PromptLoader("./prompts")
prompt = loader.load("template.txt", var1="value")
```

---

### 2. 业务服务层 (`web/services/`)

**职责：**
- 业务逻辑封装
- 不包含 API 路由逻辑

#### `preferences_loader.py` - 偏好加载服务

**根据 DESIGN.md 设计：**

```python
from crewai_web.web.services.preferences_loader import get_preferences

loader = get_preferences()

# Agent 执行时：加载系统规则 + 偏好
full_prompt = loader.load()

# 进化服务时：只读取偏好
preferences_only = loader.load_preferences_only()

# 保存偏好
loader.save_preferences(new_content)
```

**职责：**
- ✅ 加载 `.crew/system_rules.md`
- ✅ 加载 `.crew/preferences.md`
- ✅ 保存偏好内容
- ❌ **不包含**进化、提案、diff 等业务逻辑（这些在 `preferences_evolution_service.py`）

---

### 3. LLM 层 (`core/llm/`)

**职责：**
- LLM 提供商管理
- 统一 LLM 创建接口

**使用方式：**
```python
from crewai_web.core.llm import get_default_llm, get_llm_for_agent

llm = get_default_llm()
llm = get_llm_for_agent("ceo")
```

---

### 4. 工具层 (`core/tools/`)

**职责：**
- 纯工具封装
- Skills 管理

**只包含工具，不包含业务逻辑**

---

## 删除的文件

### ❌ `openai_client.py` - 已删除

**原因：**
1. 功能与 `AIClient` 重复
2. LLM Factory 已统一管理 LLM 提供商
3. 低级 SDK 封装不需要单独模块

**迁移方案：**
- 使用 `AIClient` 替代
- 使用 LLM Factory 管理提供商

---

## 业务逻辑重构建议

### 问题：Preferences 进化逻辑过于复杂

**当前问题：**
- `preferences_evolution_service.py` 包含大量进化、提案、diff 逻辑
- API 层 `/preferences/proposals` 等端点过于复杂
- 不符合 DESIGN.md 的简洁设计

**建议重构：**

#### 1. 简化 Preferences 服务

`core/services/preferences.py` **只负责：**
- 加载文件
- 保存文件
- 提供文件路径

#### 2. 进化逻辑移到 Web 层

```
web/services/
└── preferences_evolution_service.py  # 保留，但简化

web/api/
└── preferences.py  # 简化，只保留必要端点
```

#### 3. 用户输入流程

**根据你的需求：**

```python
@router.post("/generate-crew", response_model=ChatResponse)
async def generate_crew_from_chat(request: ChatRequest):
    """
    用户输入场景描述 → AI 生成 Crew
    
    流程：
    1. 接收用户输入（scenario, context）
    2. 调用 AIClient 生成 Crew 配置
    3. 返回结果
    
    不包含：
    - 偏好进化
    - 提案生成
    - Diff 对比
    """
    # 简单直接的业务逻辑
    pass
```

**偏好更新应该是独立的流程：**
- 用户手动触发
- 或者在执行完成后异步触发
- 不应该耦合在 generate-crew 中

---

## 导入路径变更

### 旧路径 → 新路径

```python
# AI Client
from crewai_web.core.ai_client import AIClient
→ from crewai_web.core.ai import AIClient

# Preferences（业务逻辑，在 web 层）
from crewai_web.core.preferences import get_preferences
→ from crewai_web.web.services.preferences_loader import get_preferences

# Protocol（技术组件，在 core 层）
from crewai_web.core.protocol import PromptToText
→ from crewai_web.core.ai import PromptToText

# Prompt Loader（技术组件，在 core 层）
from crewai_web.core.prompt_loader import PromptLoader
→ from crewai_web.core.ai import PromptLoader
```

---

## 已完成的重构

✅ 创建 `core/ai/` 目录（纯技术组件）  
✅ 移动 `AIClient` → `core/ai/client.py`  
✅ 移动 `protocol.py` → `core/ai/protocol.py`  
✅ 移动 `prompt_loader.py` → `core/ai/prompt_loader.py`  
✅ 简化 `preferences.py` → `web/services/preferences_loader.py`（业务逻辑）  
✅ 删除 `openai_client.py`（冗余）  
✅ 删除 `core/services/`（不需要，业务逻辑在 web 层）  
✅ 更新所有导入路径  

---

## 下一步建议

### 1. 简化 Preferences API

**保留端点：**
- `GET /preferences/current` - 获取当前偏好
- `PUT /preferences/update` - 更新偏好（手动）

**删除或移动：**
- `/preferences/proposals/*` - 进化提案相关（可选功能）
- `/preferences/evolve-from-execution` - 自动进化（可选）

### 2. 简化 Chat API

**`/chat/generate-crew` 应该：**
- 只接收用户输入
- 调用 AI 生成 Crew
- 返回结果
- 不包含偏好进化逻辑

### 3. 可选：独立的进化服务

如果需要偏好进化功能：
- 创建独立的 `/evolution/*` 路由
- 或者作为后台任务
- 不耦合在核心流程中

---

## 总结

**重构原则：**
1. **分层清晰** - AI 层、服务层、工具层分离
2. **职责单一** - 每个模块只做一件事
3. **简单直接** - 符合 DESIGN.md 的简洁设计
4. **易于扩展** - 新功能不影响核心流程

**核心改进：**
- ✅ AI 交互层独立
- ✅ Preferences 只负责加载
- ✅ 删除冗余的 openai_client
- ✅ 导入路径更清晰
