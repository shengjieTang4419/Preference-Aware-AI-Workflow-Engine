# Crew 生成架构设计

## 概述

本文档描述 Crew 生成引擎的架构设计思想，解释**为什么要这样设计**，以及各个组件的**职责划分**。

**核心目标**：
- Pipeline 模式编排固定生成流程
- 事件驱动架构，职责清晰
- Template Method 模式统一日志和 WebSocket 推送
- 强类型上下文传递，避免状态混乱
- 易于扩展和维护

**与 Crew 执行架构的区别**：
- **Crew 生成**：固定的 8 步流程，使用 Pipeline 模式
- **Crew 执行**：动态任务数量，使用责任链 + 策略模式

---

## 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      API 层                                   │
│  POST /chat/generate-crew                                    │
│  - 接收用户场景描述                                           │
│  - 创建执行记录                                               │
│  - 提交后台任务（BackgroundTasks）                            │
│  - 返回 execution_id                                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   WebSocket 层                                │
│  WS /chat/ws/{execution_id}                                  │
│  - 前端连接 WebSocket                                         │
│  - 接收实时进度推送                                           │
│  - 接收完成/错误通知                                          │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              CrewGenerationPipeline（编排层）                 │
│  execute(execution_id, scenario)                             │
│                                                              │
│  职责：                                                       │
│  1. 创建 EventContext（强类型上下文）                        │
│  2. 按顺序执行 8 个固定步骤                                   │
│  3. 管理执行状态（RUNNING → COMPLETED/FAILED）              │
│  4. 推送完成/错误消息到 WebSocket                            │
│                                                              │
│  固定的 8 个步骤：                                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  1. GenerateTopicEvent       → 生成项目主题          │   │
│  │  2. GenerateTasksPlanEvent   → 规划任务              │   │
│  │  3. MatchAgentsEvent         → 匹配/创建 Agents      │   │
│  │  4. CreateCrewEvent          → 创建 Crew             │   │
│  │  5. CreateTasksEvent         → 创建 Tasks            │   │
│  │  6. AssignModelsEvent        → 分配 AI 模型          │   │
│  │  7. VerifyEvent              → 复验并更新配置        │   │
│  │  8. ExecuteArtifactEvent     → 执行制品生成Skills    │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              BusinessEvent（事件基类）                        │
│  Template Method 模式                                        │
│                                                              │
│  execute(ctx):                                               │
│    1. _before(ctx)    → 日志 + WebSocket 通知（进行中）     │
│    2. do_execute(ctx) → 子类实现业务逻辑                     │
│    3. _after(ctx)     → 日志 + WebSocket 通知（完成）       │
│    4. _on_error(ctx)  → 日志 + WebSocket 通知（失败）       │
│                                                              │
│  装饰器行为（横切关注点）：                                   │
│  - execution_logger.log()  → 持久化日志                     │
│  - ws_manager.send_progress() → 推送进度到前端              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              EventContext（上下文对象）                       │
│  强类型 dataclass，在步骤间传递数据                           │
│                                                              │
│  输入（初始化时确定）：                                       │
│  - execution_id: str                                         │
│  - scenario: str                                             │
│                                                              │
│  中间产物（各步骤写入）：                                     │
│  - topic: str                                                │
│  - tasks_plan: List[dict]                                    │
│  - agents_mapping: Dict[str, str]                            │
│  - crew_id: str                                              │
│  - task_ids: List[str]                                       │
│  - agent_model_assignments: Dict[str, str]                   │
│                                                              │
│  最终结果：                                                   │
│  - error: Optional[str]                                      │
│  - to_result() → 转换为 API 响应格式                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 核心设计模式

### 1. Pipeline 模式

**为什么用 Pipeline 而不是责任链？**

| 特性 | Pipeline | 责任链 |
|------|----------|--------|
| **流程** | 固定顺序，所有步骤必须执行 | 动态流程，可中断 |
| **步骤数量** | 固定（8 步） | 动态（根据任务数量） |
| **适用场景** | Crew 生成（固定流程） | Crew 执行（动态任务） |
| **复杂度** | 简单，易理解 | 复杂，灵活 |

**Pipeline 实现**：

```python
class CrewGenerationPipeline:
    def __init__(self):
        self.events = [
            GenerateTopicEvent(),
            GenerateTasksPlanEvent(),
            MatchAgentsEvent(),
            CreateCrewEvent(),
            CreateTasksEvent(),
            AssignModelsEvent(),
            VerifyEvent(),
            ExecuteArtifactEvent(),
        ]
    
    async def execute(self, execution_id: str, scenario: str) -> dict:
        ctx = EventContext(execution_id=execution_id, scenario=scenario)
        
        for event in self.events:
            await event.execute(ctx)  # 顺序执行
        
        return ctx.to_result()
```

---

### 2. Template Method 模式

**为什么用 Template Method？**

将**横切关注点**（日志、WebSocket 推送）从业务逻辑中分离：

```python
class BusinessEvent(BaseEvent):
    async def execute(self, ctx: EventContext) -> None:
        """模板方法 - 不要覆写"""
        try:
            await self._before(ctx)      # 装饰：日志 + WebSocket
            await self.do_execute(ctx)   # 业务逻辑（子类实现）
            await self._after(ctx)       # 装饰：日志 + WebSocket
        except Exception as e:
            await self._on_error(ctx, e) # 装饰：日志 + WebSocket
            raise
    
    @abstractmethod
    async def do_execute(self, ctx: EventContext) -> None:
        """子类实现业务逻辑"""
        pass
```

**优势**：
- ✅ 业务代码只关注核心逻辑
- ✅ 日志和 WebSocket 推送自动处理
- ✅ 统一的错误处理
- ✅ 易于扩展（新增步骤只需实现 `do_execute`）

---

### 3. Context Object 模式

**为什么用强类型 dataclass 而不是 dict？**

| 方案 | 优势 | 劣势 |
|------|------|------|
| **dataclass** | 类型安全、IDE 提示、清晰 | 固定字段 |
| **dict** | 灵活 | 无类型检查、易出错 |

**选择 dataclass 的原因**：
- Crew 生成流程固定，字段确定
- 类型安全避免运行时错误
- IDE 自动补全提升开发效率

```python
@dataclass
class EventContext:
    execution_id: str
    scenario: str
    topic: Optional[str] = None
    tasks_plan: Optional[List[dict]] = None
    # ... 其他字段
```

---

## 具体步骤详解

### 步骤 1: GenerateTopicEvent

**职责**：从用户场景描述生成项目主题（10-20 字）

**输入**：
- `ctx.scenario`：用户场景描述

**输出**：
- `ctx.topic`：项目主题

**实现**：
```python
class GenerateTopicEvent(BusinessEvent):
    name = "生成项目主题"
    step = 1
    total = 8
    
    async def do_execute(self, ctx: EventContext) -> None:
        ai_client = AIClient.get_default()
        prompt = ai_client.load_prompt("generator/topic.prompt", scenario=ctx.scenario)
        topic = await ai_client.call(prompt, role=self.role)
        ctx.topic = topic.strip()
```

---

### 步骤 2: GenerateTasksPlanEvent

**职责**：根据场景和主题规划 1-5 个任务

**输入**：
- `ctx.scenario`
- `ctx.topic`

**输出**：
- `ctx.tasks_plan`：任务规划列表

**实现**：
```python
class GenerateTasksPlanEvent(BusinessEvent):
    name = "规划任务"
    step = 2
    total = 8
    
    async def do_execute(self, ctx: EventContext) -> None:
        ctx.tasks_plan = await task_generator.generate_tasks_plan(
            ctx.scenario, ctx.topic, None
        )
```

---

### 步骤 3: MatchAgentsEvent

**职责**：为每个任务匹配或创建 Agent

**输入**：
- `ctx.tasks_plan`

**输出**：
- `ctx.agents_mapping`：`{task_name: agent_id}` 映射

**实现**：
```python
class MatchAgentsEvent(BusinessEvent):
    name = "匹配 Agents"
    step = 3
    total = 8
    
    async def do_execute(self, ctx: EventContext) -> None:
        ctx.agents_mapping = await agent_generator.match_or_create_agents(
            ctx.tasks_plan
        )
```

---

### 步骤 4: CreateCrewEvent

**职责**：创建 Crew 记录（先创建，后续步骤会更新）

**输入**：
- `ctx.topic`
- `ctx.agents_mapping`

**输出**：
- `ctx.crew_id`：Crew ID

**实现**：
```python
class CreateCrewEvent(BusinessEvent):
    name = "创建 Crew"
    step = 4
    total = 8
    
    async def do_execute(self, ctx: EventContext) -> None:
        crew_data = CrewCreate(
            name=ctx.topic,
            description=f"AI 自动生成的 Crew：{ctx.topic}",
            agent_ids=list(ctx.agents_mapping.values()),
            task_ids=[],  # 稍后更新
            process_type="sequential",
        )
        created_crew = crew_service.create_crew(crew_data)
        ctx.crew_id = created_crew.id
```

---

### 步骤 5: CreateTasksEvent

**职责**：创建 Task 记录

**输入**：
- `ctx.tasks_plan`
- `ctx.agents_mapping`
- `ctx.topic`
- `ctx.crew_id`
- `ctx.execution_id`

**输出**：
- `ctx.task_ids`：Task ID 列表

**实现**：
```python
class CreateTasksEvent(BusinessEvent):
    name = "创建 Tasks"
    step = 5
    total = 8
    
    async def do_execute(self, ctx: EventContext) -> None:
        ctx.task_ids = task_generator.create_tasks(
            ctx.tasks_plan,
            ctx.agents_mapping,
            topic=ctx.topic,
            crew_id=ctx.crew_id,
            execution_id=ctx.execution_id,
        )
```

---

### 步骤 6: AssignModelsEvent

**职责**：为每个 Agent 分配最优 AI 模型

**输入**：
- `ctx.topic`
- `ctx.agents_mapping`
- `ctx.task_ids`

**输出**：
- `ctx.agent_model_assignments`：`{agent_id: model_tier}` 映射

**实现**：
```python
class AssignModelsEvent(BusinessEvent):
    name = "分配 AI 模型"
    step = 6
    total = 8
    
    async def do_execute(self, ctx: EventContext) -> None:
        ctx.agent_model_assignments = await model_assignment_service.assign_models_for_crew(
            crew_name=ctx.topic,
            process_type="sequential",
            agent_ids=list(ctx.agents_mapping.values()),
            task_ids=ctx.task_ids,
        )
```

---

### 步骤 7: VerifyEvent

**职责**：复验并更新 Crew 配置

**输入**：
- `ctx.crew_id`
- `ctx.task_ids`
- `ctx.agent_model_assignments`

**输出**：
- 无（更新数据库）

**实现**：
```python
class VerifyEvent(BusinessEvent):
    name = "复验配置"
    step = 7
    total = 8
    
    async def do_execute(self, ctx: EventContext) -> None:
        crew_service.update_crew(
            ctx.crew_id,
            CrewUpdate(
                task_ids=ctx.task_ids,
                agent_model_assignments=ctx.agent_model_assignments,
            ),
        )
```

### 步骤 8: ExecuteArtifactEvent

**职责**：执行制品生成Skills，生成最终产出物

**输入**：
- `ctx.scenario` — 用户场景描述
- `ctx.execution_id` — 执行ID
- `ctx.crew_output` — Crew执行的文本输出（如果有）

**输出**：
- `ctx.artifact_skills` — 匹配到的skills列表
- `ctx.artifact_result` — 制品最终结果

**实现**：
```python
class ExecuteArtifactEvent(BusinessEvent):
    name = "生成制品"
    step = 8
    total = 8

    async def do_execute(self, ctx: EventContext) -> None:
        # 1. 匹配artifact skills
        matched = await match_artifact_skills(ctx.scenario, ctx.scenario)
        ctx.artifact_skills = [s["name"] for s in matched]

        # 2. 执行skill链
        chain = get_skill_chain()
        result = await chain.execute(
            skill_names=ctx.artifact_skills,
            crew_output=ctx.crew_output or ctx.scenario,
            execution_id=ctx.execution_id,
        )

        # 3. 保存结果
        ctx.artifact_result = result.dict()
```

---

## 横切关注点处理

### 1. 日志持久化

**工具**：`ExecutionLogger`

```python
class ExecutionLogger:
    @staticmethod
    def log(execution_id: str, level: str, message: str, source: str = "crew.generation"):
        execution_log_service.add_log(execution_id, level, message, source)
```

**调用时机**：
- `_before()`：记录步骤开始
- `_after()`：记录步骤完成
- `_on_error()`：记录错误

---

### 2. WebSocket 推送

**工具**：`WebSocketManager`

```python
class WebSocketManager:
    async def send_progress(self, execution_id: str, message: str, step: int, total: int, status: str):
        """推送进度消息"""
        
    async def send_complete(self, execution_id: str, result: dict):
        """推送完成消息"""
        
    async def send_error(self, execution_id: str, error: str):
        """推送错误消息"""
```

**消息格式**：
```json
{
  "type": "progress",
  "message": "⏳ 生成项目主题...",
  "step": 1,
  "total": 8,
  "status": "running",
  "percentage": 14
}
```

---

## 执行流程时序图

```
用户                API                Pipeline              Event                WebSocket
 │                  │                   │                     │                     │
 │─POST /generate───▶│                   │                     │                     │
 │                  │                   │                     │                     │
 │◀─execution_id────│                   │                     │                     │
 │                  │                   │                     │                     │
 │─WS /ws/{id}──────┼───────────────────┼─────────────────────┼────────────────────▶│
 │                  │                   │                     │                     │
 │                  │─BackgroundTask───▶│                     │                     │
 │                  │                   │                     │                     │
 │                  │                   │─update_status(RUNNING)                    │
 │                  │                   │                     │                     │
 │                  │                   │─[1] GenerateTopic──▶│                     │
 │                  │                   │                     │─_before()──────────▶│
 │◀─────────────────┼───────────────────┼─────────────────────┼─"⏳ 生成项目主题..."─│
 │                  │                   │                     │                     │
 │                  │                   │                     │─do_execute()        │
 │                  │                   │                     │  (调用 AI)          │
 │                  │                   │                     │                     │
 │                  │                   │                     │─_after()───────────▶│
 │◀─────────────────┼───────────────────┼─────────────────────┼─"✅ 主题生成完成"───│
 │                  │                   │                     │                     │
 │                  │                   │─[2] GenerateTasksPlan▶│                   │
 │◀─────────────────┼───────────────────┼─────────────────────┼─"⏳ 规划任务..."────│
 │                  │                   │                     │                     │
 │                  │                   │                     │  ... (执行)         │
 │                  │                   │                     │                     │
 │◀─────────────────┼───────────────────┼─────────────────────┼─"✅ 任务规划完成"───│
 │                  │                   │                     │                     │
 │                  │                   │  ... (步骤 3-7)      │                     │
 │                  │                   │                     │                     │
 │                  │                   │─send_complete()─────┼────────────────────▶│
 │◀─────────────────┼───────────────────┼─────────────────────┼─{"type":"complete"}─│
 │                  │                   │                     │                     │
 │                  │                   │─update_status(COMPLETED)                  │
```

---

## 错误处理

### 1. 步骤失败

```python
async def execute(self, ctx: EventContext) -> None:
    try:
        await self._before(ctx)
        await self.do_execute(ctx)  # 业务逻辑可能抛异常
        await self._after(ctx)
    except Exception as e:
        await self._on_error(ctx, e)  # 记录日志 + 推送错误
        raise  # 向上传播，终止 Pipeline
```

### 2. Pipeline 失败

```python
async def execute(self, execution_id: str, scenario: str) -> dict:
    try:
        for event in self.events:
            await event.execute(ctx)
        
        await ws_manager.send_complete(execution_id, ctx.to_result())
        execution_log_service.update_status(execution_id, ExecutionStatus.COMPLETED)
    
    except Exception as e:
        ctx.error = str(e)
        await ws_manager.send_error(execution_id, ctx.error)
        execution_log_service.update_status(execution_id, ExecutionStatus.FAILED)
        raise
```

---

## 与 Crew 执行架构对比

| 维度 | Crew 生成 | Crew 执行 |
|------|-----------|-----------|
| **目标** | 生成 Crew 配置 | 执行 Crew 任务 |
| **流程** | 固定 8 步 | 动态（根据任务数） |
| **模式** | Pipeline | 责任链 + 策略 |
| **上下文** | EventContext（dataclass） | ExecutionContext（dict-like） |
| **调度** | 顺序执行 | Sequential/Hierarchical |
| **通知** | WebSocket 实时推送 | 邮件/钉钉通知 |
| **状态管理** | PENDING → RUNNING → COMPLETED | 同左 |

---

## 扩展指南

### 新增生成步骤

1. 创建新的 Event 类：

```python
class NewStepEvent(BusinessEvent):
    name = "新步骤"
    step = 8  # 更新步骤号
    total = 8  # 更新总步骤数
    
    async def do_execute(self, ctx: EventContext) -> None:
        # 实现业务逻辑
        ctx.new_field = await some_service.do_something()
```

2. 更新 `EventContext`：

```python
@dataclass
class EventContext:
    # ... 现有字段
    new_field: Optional[str] = None
```

3. 注册到 Pipeline：

```python
class CrewGenerationPipeline:
    def __init__(self):
        self.events = [
            # ... 现有步骤
            NewStepEvent(),  # 新增
        ]
```

4. 更新所有步骤的 `total` 属性为新的总步骤数

---

## 文件结构

```
crewai_web/
├── core/
│   ├── event/                      # 事件框架
│   │   ├── __init__.py
│   │   ├── base_event.py          # BaseEvent 抽象基类
│   │   ├── business_event.py      # BusinessEvent 模板方法
│   │   └── event_context.py       # EventContext 上下文对象
│   └── tools/
│       ├── websocket_manager.py   # WebSocket 管理器
│       └── execution_logger.py    # 日志工具
│
├── web/
│   ├── api/
│   │   └── chat.py                # API 入口
│   ├── events/                    # 具体业务事件
│   │   ├── __init__.py
│   │   ├── generate_topic_event.py
│   │   ├── generate_tasks_plan_event.py
│   │   ├── match_agents_event.py
│   │   ├── create_crew_event.py
│   │   ├── create_tasks_event.py
│   │   ├── assign_models_event.py
│   │   └── verify_event.py
│   └── services/
│       ├── crew_generation_pipeline.py  # Pipeline 编排
│       └── ai_generator_service.py      # 向后兼容入口
│
└── prompts/
    └── generator/
        ├── topic.prompt           # Topic 生成提示词
        └── tasks.prompt           # Tasks 生成提示词
```

---

## 总结

**核心设计原则**：
1. **职责单一**：每个 Event 只做一件事
2. **关注点分离**：业务逻辑与日志/通知分离
3. **类型安全**：强类型上下文避免运行时错误
4. **易于扩展**：新增步骤只需实现 `do_execute`
5. **固定流程**：Pipeline 模式适合固定步骤

**与执行架构的协同**：
- **生成**：创建 Crew 配置（本文档）
- **执行**：运行 Crew 任务（见 `CREW_EXECUTION_ARCHITECTURE.md`）
