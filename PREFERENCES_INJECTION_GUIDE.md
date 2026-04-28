# 偏好注入机制详解

## 问题背景

在 AI 交互中，有两种不同的场景：

### 场景 1：系统内置 AI 交互

- **特点**：prompt 由开发者编写，存放在 `prompts/` 目录下
- **目的**：生成 Topic、拆解 Tasks、创建 Agent、推荐 Skills 等
- **需求**：**不需要**注入用户偏好和系统规则
- **原因**：这些是系统内部操作，prompt 已经包含了所有必要的指令

**示例**：
```python
# Topic 生成
prompt = client.load_prompt("generator/topic.prompt", scenario="开发博客系统")
response = await client.call_structured(prompt, TopicResponse)
# ❌ 不需要注入偏好规则
```

### 场景 2：Crew 动态编排

- **特点**：Agent 执行用户的动态任务
- **目的**：完成用户的实际需求（如编写代码、分析数据）
- **需求**：**需要**注入用户偏好和系统规则
- **原因**：需要根据用户的个人偏好来执行任务

**示例**：
```python
# Agent 执行任务
agent = CrewAIAgent(role="产品经理", goal="设计产品方案", llm=llm)
# ✅ 需要注入偏好规则，让 Agent 了解用户的设计偏好
```

## 解决方案

### 1. 添加 `inject_preferences` 参数

`@/workspaces/one_person_company/crewai_web/core/ai/client.py:84-118`

```python
async def call(
    self,
    prompt: str,
    response_model: Type[T],
    system_prompt: Optional[str] = None,
    role: Optional[str] = None,
    inject_preferences: bool = False,  # 🆕 新增参数
    max_retries: int = 3
) -> T:
    """
    调用 LLM 并返回结构化响应
    
    Args:
        inject_preferences: 是否注入偏好规则和系统规则（默认 False）
            - False: 系统内置 AI 交互（prompts 下的 prompt）
            - True: Crew 动态编排（需要偏好规则）
    """
    # 只有在明确要求注入偏好时才加载
    if inject_preferences and system_prompt is None:
        preferences = get_preferences()
        system_prompt = preferences.load()
    
    # 组装完整 prompt
    if system_prompt:
        full_prompt = f"{system_prompt}\n\n{prompt}"
    else:
        full_prompt = prompt
```

### 2. 两种场景的使用方式

#### 场景 1：系统内置 AI 交互（默认行为）

```python
# Topic 生成
prompt = client.load_prompt("generator/topic.prompt", scenario="开发博客系统")
response = await client.call_structured(
    prompt=prompt,
    response_model=TopicResponse
    # inject_preferences=False  # 默认值，不注入偏好
)

# 发送给 LLM 的 prompt：
"""
# Role: 你是一名资深项目管理专家

## Task
根据以下场景，生成一个简洁的项目主题：

场景描述：开发博客系统
"""
```

#### 场景 2：Crew 动态编排（显式启用）

```python
# Agent 执行任务
task_prompt = "请设计一个电商系统的产品方案"
response = await client.call_structured(
    prompt=task_prompt,
    response_model=ProductPlan,
    inject_preferences=True  # 🔑 显式启用偏好注入
)

# 发送给 LLM 的 prompt：
"""
# 系统规则（来自 .crew/system_rules.md）
- 输出必须是有效的 JSON 格式
- 使用中文回答

# 个人偏好（来自 .crew/preferences.md）
- 优先选择熟悉的技术栈
- 性能和可读性冲突时，优先可读性

请设计一个电商系统的产品方案
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
│   │   ├── topic.prompt          # ❌ 不注入偏好
│   │   ├── tasks.prompt          # ❌ 不注入偏好
│   │   ├── agent.prompt          # ❌ 不注入偏好
│   │   ├── agent_match.prompt    # ❌ 不注入偏好
│   │   └── skills_recommendation.prompt  # ❌ 不注入偏好
│   │
│   └── preferences/
│       ├── evolution.prompt      # ❌ 不注入偏好
│       └── diff_summary.prompt   # ❌ 不注入偏好
│
└── crewai_web/
    └── web/
        └── services/
            ├── ai_generator_service.py  # ❌ 不注入偏好
            ├── agent_generator.py       # ❌ 不注入偏好
            ├── task_generator.py        # ❌ 不注入偏好
            └── skills_recommender.py    # ❌ 不注入偏好
```

## 代码示例

### 系统内置 AI 交互（不注入偏好）

```python
# crewai_web/web/services/ai_generator_service.py

class AIGeneratorService:
    async def generate_topic(self, scenario: str, context: str = "") -> str:
        """生成项目主题"""
        prompt = self.ai_client.load_prompt(
            "generator/topic.prompt",
            scenario=scenario,
            context_section=context
        )
        
        # ❌ 不注入偏好（使用默认值 inject_preferences=False）
        response = await self.ai_client.call_structured(
            prompt=prompt,
            response_model=TopicResponse
        )
        
        return response.topic

    async def generate_tasks(self, topic: str, scenario: str) -> List[Dict]:
        """拆解任务"""
        prompt = self.ai_client.load_prompt(
            "generator/tasks.prompt",
            topic=topic,
            scenario=scenario
        )
        
        # ❌ 不注入偏好
        response = await self.ai_client.call_structured(
            prompt=prompt,
            response_model=TasksPlanResponse
        )
        
        return response.tasks
```

### Crew 动态编排（注入偏好）

```python
# 未来实现：Crew 执行时注入偏好

class CrewExecutor:
    async def execute_task(self, agent: Agent, task: Task) -> str:
        """执行 Agent 任务"""
        task_prompt = f"""
你是 {agent.role}，你的目标是：{agent.goal}

请完成以下任务：
{task.description}

期望输出：
{task.expected_output}
"""
        
        # ✅ 注入偏好（Agent 需要了解用户的个人偏好）
        response = await self.ai_client.call_text(
            prompt=task_prompt,
            inject_preferences=True  # 🔑 显式启用
        )
        
        return response
```

## PreferencesLoader 详解

### `__init__` 方法

```python
class PreferencesLoader:
    def __init__(self, project_root: Optional[Path] = None):
        """
        初始化偏好加载器
        
        Args:
            project_root: 项目根目录（可选，默认自动查找）
        """
        # 1. 自动查找项目根目录
        if project_root is None:
            current = Path(__file__).parent
            while current != current.parent:
                # 查找 .crew 目录或 pyproject.toml 文件
                if (current / ".crew").exists() or (current / "pyproject.toml").exists():
                    project_root = current
                    break
                current = current.parent
            else:
                project_root = Path.cwd()
        
        # 2. 设置对象属性（在 __init__ 中声明）
        self.project_root = project_root
        self.system_rules_file = project_root / ".crew" / "system_rules.md"
        self.preferences_file = project_root / ".crew" / "preferences.md"
        self._cache: Optional[str] = None
        
        # 3. 输出日志
        logger.info(f"Preferences loader: {self.system_rules_file}, {self.preferences_file}")
```

### `load()` 方法

```python
def load(self, force_reload: bool = False) -> str:
    """
    加载系统规则 + 个人偏好
    
    为什么不需要参数？
    因为文件路径已经在 __init__ 中设置为对象属性了！
    """
    # 使用 __init__ 中设置的属性
    if self.system_rules_file.exists():
        system_rules = self.system_rules_file.read_text()
    
    if self.preferences_file.exists():
        preferences = self.preferences_file.read_text()
    
    return "\n\n".join([system_rules, preferences])
```

### 为什么 `load()` 不需要声明文件路径？

```python
# 创建对象时，__init__ 已经设置了文件路径
loader = PreferencesLoader()
# 此时 loader.system_rules_file 和 loader.preferences_file 已经有值了

# 调用 load() 时，直接使用对象属性
content = loader.load()
# load() 方法内部使用 self.system_rules_file 和 self.preferences_file
# 不需要再传参数！
```

这就是面向对象编程的核心思想：
- **`__init__`**：设置对象的初始状态（属性）
- **其他方法**：使用对象的属性进行操作

## 对比表

| 场景 | 注入偏好 | 原因 | 示例 |
|------|---------|------|------|
| Topic 生成 | ❌ 否 | 系统内部操作，prompt 已完整 | `generate_topic()` |
| Tasks 拆解 | ❌ 否 | 系统内部操作，prompt 已完整 | `generate_tasks()` |
| Agent 创建 | ❌ 否 | 系统内部操作，prompt 已完整 | `create_agent()` |
| Agent 匹配 | ❌ 否 | 系统内部操作，prompt 已完整 | `match_agent()` |
| Skills 推荐 | ❌ 否 | 系统内部操作，prompt 已完整 | `recommend_skills()` |
| 偏好进化 | ❌ 否 | 分析执行结果，不需要偏好 | `evolve_preferences()` |
| **Crew 执行** | ✅ 是 | Agent 执行用户任务，需要偏好 | `execute_task()` |

## 最佳实践

### 1. 系统内置 AI 交互

```python
# ✅ 正确：不注入偏好
prompt = client.load_prompt("generator/topic.prompt", ...)
response = await client.call_structured(prompt, TopicResponse)

# ❌ 错误：不应该注入偏好
response = await client.call_structured(prompt, TopicResponse, inject_preferences=True)
```

### 2. Crew 动态编排

```python
# ✅ 正确：注入偏好
response = await client.call_text(task_prompt, inject_preferences=True)

# ❌ 错误：应该注入偏好
response = await client.call_text(task_prompt)  # 缺少用户偏好
```

### 3. 自定义 System Prompt

```python
# 如果需要自定义 system prompt，可以直接传入
custom_system = "你是一个专业的代码审查专家"
response = await client.call_structured(
    prompt=task_prompt,
    response_model=ReviewResult,
    system_prompt=custom_system  # 自定义 system prompt
    # inject_preferences 会被忽略
)
```

## 总结

### 核心改进

1. ✅ 添加 `inject_preferences` 参数，默认为 `False`
2. ✅ 系统内置 AI 交互不注入偏好（保持 prompt 纯净）
3. ✅ Crew 动态编排时显式启用偏好注入
4. ✅ 支持自定义 system prompt（覆盖偏好）

### 设计原则

- **默认不注入**：系统内置操作不需要用户偏好
- **显式启用**：Crew 执行时明确需要偏好
- **灵活可控**：支持自定义 system prompt

### 为什么这样设计？

1. **职责分离**：
   - 系统内置 AI：生成 Crew 配置（不需要偏好）
   - Crew 执行：完成用户任务（需要偏好）

2. **Prompt 纯净**：
   - 系统 prompt 已经包含完整指令
   - 不需要额外的偏好规则

3. **用户体验**：
   - 偏好只影响最终输出
   - 不影响 Crew 的生成过程

---

**更新时间**: 2026-04-26  
**核心理念**: 场景分离，按需注入，保持 prompt 纯净
