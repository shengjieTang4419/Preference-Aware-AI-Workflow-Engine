# Crew 执行架构设计

## 概述

本文档描述 Crew 执行引擎的架构设计思想，解释**为什么要这样设计**，以及各个组件的**职责划分**。

**核心目标**：
- 责任链模式编排执行流程
- 清晰的事件驱动架构
- 支持多种调度策略（Sequential、Hierarchical）
- 动态模型分配（不同 Agent 使用不同模型）
- 易于扩展和维护

---

## 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      API 层                                   │
│  POST /api/executions                                        │
│  - 接收用户请求                                               │
│  - 创建 Execution 记录                                        │
│  - 触发异步执行                                               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   异步执行层                                  │
│  run_crew_async()                                            │
│  - 在线程池中执行（避免阻塞事件循环）                          │
│  - 执行完成后触发偏好进化                                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   同步执行层                                  │
│  _sync_run_crew()                                            │
│  - 构建 ExecutionContext                                     │
│  - 构建并执行责任链                                           │
│  - 处理执行结果和异常                                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              责任链引擎（EventChain）                         │
│  build_default_chain().execute(ctx)                          │
│                                                              │
│  固定的 4 个节点：                                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  1. PreHandleEvent    → 加载配置                     │   │
│  │  2. BusinessEventDispatcher → 业务调度（核心）       │   │
│  │  3. FinishEvent       → 保存结果                     │   │
│  │  4. TouchEvent        → 发送通知                     │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│          BusinessEventDispatcher（业务调度器）                │
│  职责：编排业务执行                                           │
│  1. 生成 BusinessEvent 列表（每个 Task 一个 Event）          │
│  2. 选择调度策略（Sequential/Hierarchical）                  │
│  3. 交给 Strategy 执行                                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              SchedulingStrategy（调度策略）                   │
│  ┌──────────────────┐         ┌────────────────────────┐   │
│  │ Sequential       │         │  Hierarchical          │   │
│  │ 顺序执行         │         │  层级执行              │   │
│  └──────────────────┘         └────────────────────────┘   │
│                                                              │
│  职责：                                                       │
│  1. 从 agent_model_assignments 获取模型分配                  │
│  2. 为每个 Agent 构建 CrewAI Agent 对象                      │
│  3. 为每个 Task 构建 CrewAI Task 对象                        │
│  4. 创建 Crew 并执行                                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  CrewBuilder（构建器）                        │
│  职责：从配置创建 CrewAI 对象                                 │
│  - build_agent(agent_config, inputs, model_tier)            │
│  - build_task(task_config, agent, context_tasks)            │
│  - _get_llm_for_tier(model_tier) → 动态模型选择              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   AIClient（模型客户端）                      │
│  - get_default() → 默认模型                                  │
│  - create(model=xxx) → 指定模型                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 设计思想

### 1. 为什么使用责任链模式？

**问题**：如果没有责任链，执行流程会是一堆 if-else：
- 难以扩展（新增步骤需要修改主流程）
- 难以维护（逻辑分散）
- 难以测试（无法单独测试某个步骤）

**解决方案**：责任链模式
```
PreHandleEvent → BusinessEventDispatcher → FinishEvent → TouchEvent
```

**好处**：
- **单一职责**：每个 Event 只做一件事
- **易于扩展**：新增步骤只需添加新的 Event
- **易于测试**：每个 Event 可以独立测试
- **清晰的流程**：一眼看出执行顺序

---

### 2. 为什么需要 ExecutionContext？

**设计原则**：**上下文对象模式**

**职责**：
- 在责任链中传递共享状态
- 每个 Event 可以读取和写入 Context
- 下一个 Event 可以看到上一个的修改

**为什么不用全局变量？**
- **线程安全**：每个执行有独立的 Context
- **易于测试**：可以构造测试用的 Context
- **清晰的数据流**：明确知道哪些数据在传递

**Context 包含什么？**
- **输入参数**：crew_id, requirement, inputs, exec_id
- **中间状态**：crew_config, agent_configs, task_configs
- **执行结果**：result, success, error
- **指标数据**：start_time, end_time, task_completed
- **日志**：logs 列表

---

### 3. 为什么需要 BusinessEventDispatcher？

**设计原则**：**调度器模式**

**职责**：
- 从配置生成 N 个 BusinessEvent（每个 Task 一个）
- 选择调度策略（根据 process_type）
- 把 BusinessEvent 列表交给 Strategy 执行

**为什么不直接在 EventChain 中执行业务逻辑？**
- **分离关注点**：EventChain 负责流程，Dispatcher 负责调度
- **易于扩展**：新增调度策略不影响 EventChain
- **清晰的职责**：Dispatcher 是业务执行的入口

**Dispatcher 做了什么？**
```
1. 读取 crew_config.task_ids
2. 为每个 task_id 创建 BusinessEvent(task_id, agent_config, task_config)
3. 根据 process_type 选择 Strategy（Sequential/Hierarchical）
4. 调用 strategy.schedule(business_events, ctx)
```

---

### 4. 为什么需要 SchedulingStrategy？

**设计原则**：**策略模式**

**职责**：
- 决定 BusinessEvent 的执行顺序
- 构建 CrewAI 的 Agent 和 Task
- 执行 Crew

**为什么不直接在 Dispatcher 中执行？**
- **开闭原则**：新增策略不需要修改 Dispatcher
- **单一职责**：Dispatcher 负责调度，Strategy 负责执行
- **易于测试**：每个 Strategy 可以独立测试

**策略注册表**：
```
STRATEGY_REGISTRY = {
    "sequential": SequentialStrategy,
    "hierarchical": HierarchicalStrategy,
}
```

**如何选择策略？**
```
process_type = ctx.crew_config.process_type  # "sequential" 或 "hierarchical"
strategy = get_strategy(process_type)
```

---

### 5. 为什么需要 CrewBuilder？

**设计原则**：**Builder 模式**

**职责**：
- 从配置创建 CrewAI Agent 对象
- 从配置创建 CrewAI Task 对象
- 根据 model_tier 动态选择模型

**为什么不让 Strategy 直接创建？**
- **单一职责**：Strategy 负责调度，Builder 负责构建
- **代码复用**：所有 Strategy 都用同一个 Builder
- **易于测试**：可以单独测试 Builder

**Builder 的核心逻辑**：
```
build_agent(agent_config, inputs, model_tier):
  1. 根据 model_tier 获取 LLM（动态模型选择）
  2. 替换 role/goal/backstory 中的占位符
  3. 获取 Agent 的 skills
  4. 创建 CrewAI Agent 对象
```

---

### 6. 为什么需要动态模型分配？

**业务需求**：不同 Agent 使用不同档位的模型
- 核心 Agent（架构设计师）→ advanced 模型（qwen3.6-max-preview）
- 辅助 Agent（文档编写）→ basic 模型（qwen3.5-plus）

**配置示例**：
```
{
  "agent_model_assignments": {
    "顶层架构设计师": "advanced",
    "技术布道师": "basic",
    "竞品商业分析师": "basic",
    "营销专家": "basic"
  }
}
```

**执行流程**：
```
Strategy 中：
  agent_model_assignments = ctx.crew_config.agent_model_assignments
  for each agent:
    model_tier = agent_model_assignments.get(agent_id)
    agent = builder.build_agent(agent_config, inputs, model_tier)

CrewBuilder 中：
  _get_llm_for_tier(model_tier):
    tier_config = config_loader.get_model_config_by_default_provider(model_tier)
    model_name = tier_config["model"]
    return AIClient.create(model=model_name).llm
```

**为什么不在配置中直接写模型名？**
- **抽象层次**：业务层只关心"档位"，不关心具体模型
- **易于切换**：切换 Provider 只需修改 llm_settings.json
- **统一管理**：所有模型配置集中在一个地方

---

## 职责划分

### API 层
- **职责**：接收请求，创建 Execution 记录
- **依赖**：execution_service
- **不关心**：如何执行 Crew

### 异步执行层（run_crew_async）
- **职责**：在线程池中执行，避免阻塞
- **触发**：偏好进化（执行成功后）
- **不关心**：Crew 如何执行

### 同步执行层（_sync_run_crew）
- **职责**：构建 Context，执行责任链，处理结果
- **依赖**：EventChain
- **不关心**：责任链内部如何执行

### EventChain（责任链引擎）
- **职责**：按顺序执行 4 个固定节点
- **提供**：execute(ctx) 方法
- **处理**：异常时执行收尾节点
- **不关心**：每个节点的内部逻辑

### PreHandleEvent
- **职责**：加载配置（crew_config, agent_configs, task_configs）
- **写入**：ctx.crew_config, ctx.agent_configs, ctx.task_configs
- **不关心**：配置如何被使用

### BusinessEventDispatcher
- **职责**：生成 BusinessEvent，选择 Strategy，执行
- **读取**：ctx.crew_config, ctx.agent_configs, ctx.task_configs
- **写入**：ctx.result, ctx.success, ctx.metrics
- **不关心**：Strategy 如何执行

### FinishEvent
- **职责**：保存执行结果到数据库
- **读取**：ctx.result, ctx.success, ctx.error
- **不关心**：结果如何生成

### TouchEvent
- **职责**：发送执行完成通知
- **读取**：ctx.exec_id, ctx.success
- **不关心**：通知如何发送

### SchedulingStrategy
- **职责**：编排 BusinessEvent 的执行顺序
- **依赖**：CrewBuilder
- **实现**：SequentialStrategy, HierarchicalStrategy
- **不关心**：Agent 和 Task 如何构建

### CrewBuilder
- **职责**：从配置创建 CrewAI 对象
- **依赖**：AIClient, config_loader
- **提供**：build_agent, build_task
- **不关心**：Agent 和 Task 如何被使用

---

## 设计原则总结

### 1. 责任链模式
- 固定的 4 个节点，清晰的执行流程
- 每个节点单一职责，易于扩展

### 2. 策略模式
- 支持多种调度策略（Sequential、Hierarchical）
- 新增策略只需实现接口并注册

### 3. 上下文对象模式
- ExecutionContext 在责任链中传递状态
- 线程安全，易于测试

### 4. Builder 模式
- CrewBuilder 负责构建 CrewAI 对象
- 代码复用，易于维护

### 5. 配置驱动
- agent_model_assignments 配置模型分配
- llm_settings.json 配置具体模型
- 修改配置不需要改代码

### 6. 单一职责原则
- 每个类只做一件事
- EventChain 负责流程，Dispatcher 负责调度，Strategy 负责执行

### 7. 开闭原则
- 对扩展开放：新增 Event、新增 Strategy
- 对修改封闭：修改配置不需要改代码

---

## 执行流程详解

### 完整流程

```
1. API 接收请求
   POST /api/executions
   ↓
2. 创建 Execution 记录
   execution_service.create_execution()
   ↓
3. 异步执行
   asyncio.create_task(run_crew_async())
   ↓
4. 线程池执行
   loop.run_in_executor(_sync_run_crew)
   ↓
5. 构建 Context
   ExecutionContext(crew_id, requirement, inputs, ...)
   ↓
6. 构建责任链
   chain = build_default_chain()
   ↓
7. 执行责任链
   ctx = chain.execute(ctx)
   ↓
   ┌─────────────────────────────────────┐
   │ 7.1 PreHandleEvent                  │
   │   - 加载 crew_config                │
   │   - 加载 agent_configs              │
   │   - 加载 task_configs               │
   └─────────────────────────────────────┘
   ↓
   ┌─────────────────────────────────────┐
   │ 7.2 BusinessEventDispatcher         │
   │   - 生成 BusinessEvent 列表         │
   │   - 选择 Strategy                   │
   │   - 执行 strategy.schedule()        │
   │     ↓                                │
   │     ┌───────────────────────────┐   │
   │     │ Strategy.schedule()       │   │
   │     │ - 获取 model_assignments  │   │
   │     │ - 构建 Agents             │   │
   │     │ - 构建 Tasks              │   │
   │     │ - 创建 Crew               │   │
   │     │ - crew.kickoff()          │   │
   │     └───────────────────────────┘   │
   └─────────────────────────────────────┘
   ↓
   ┌─────────────────────────────────────┐
   │ 7.3 FinishEvent                     │
   │   - 保存执行结果                    │
   └─────────────────────────────────────┘
   ↓
   ┌─────────────────────────────────────┐
   │ 7.4 TouchEvent                      │
   │   - 发送通知                        │
   └─────────────────────────────────────┘
   ↓
8. 返回结果
   (success, logs, error)
   ↓
9. 触发偏好进化（如果成功）
   asyncio.create_task(_generate_evolution_proposal())
```

---

### 模型分配流程

```
1. Crew 配置中定义模型分配
   {
     "agent_model_assignments": {
       "顶层架构设计师": "advanced",
       "技术布道师": "basic"
     }
   }
   ↓
2. Strategy 读取配置
   agent_model_assignments = ctx.crew_config.agent_model_assignments
   ↓
3. 为每个 Agent 获取档位
   model_tier = agent_model_assignments.get("顶层架构设计师")
   # → "advanced"
   ↓
4. 调用 CrewBuilder
   builder.build_agent(agent_config, inputs, model_tier="advanced")
   ↓
5. CrewBuilder 获取模型配置
   tier_config = config_loader.get_model_config_by_default_provider("advanced")
   # → {"model": "qwen3.6-max-preview", "temperature": 0.7}
   ↓
6. 创建 AIClient
   client = AIClient.create(model="qwen3.6-max-preview")
   # provider=None → 自动使用 default_provider
   # temperature 不传 → 自动从配置读取
   ↓
7. 获取 LLM
   llm = client.llm
   ↓
8. 创建 Agent
   Agent(role=..., goal=..., llm=llm)
```

---

## 扩展性

### 新增 Event（3 步）

**步骤1**：创建 Event 类
- 继承 `BaseEvent`
- 实现 `handle(ctx)` 方法

**步骤2**：添加到责任链
- 在 `build_default_chain()` 中添加

**步骤3**：测试
- 单独测试 Event
- 集成测试责任链

**无需修改**：
- ❌ 不需要修改其他 Event
- ❌ 不需要修改 EventChain 引擎

---

### 新增 Strategy（3 步）

**步骤1**：创建 Strategy 类
- 继承 `SchedulingStrategy`
- 实现 `schedule(events, ctx)` 方法

**步骤2**：注册 Strategy
- 使用 `@register_strategy("strategy_name")` 装饰器

**步骤3**：配置使用
- 在 crew_config 中设置 `process_type="strategy_name"`

**无需修改**：
- ❌ 不需要修改 BusinessEventDispatcher
- ❌ 不需要修改其他 Strategy

---

### 新增模型档位（1 步）

**步骤**：修改配置文件
- 在 `llm_settings.json` 中添加新档位
- 在 `agent_model_assignments` 中使用新档位

**无需修改**：
- ❌ 不需要修改任何代码

---

## 架构优势

### 1. 清晰的执行流程
- 责任链模式，一眼看出执行顺序
- 每个节点职责明确

### 2. 易于扩展
- 新增 Event 不影响其他节点
- 新增 Strategy 不影响 Dispatcher
- 新增模型档位只需修改配置

### 3. 易于维护
- 单一职责，每个类只做一件事
- 代码复用，Builder 被所有 Strategy 使用

### 4. 易于测试
- 每个 Event 可以独立测试
- 每个 Strategy 可以独立测试
- 可以 Mock Context 和依赖

### 5. 灵活的模型分配
- 业务层只关心"档位"
- 配置层决定具体模型
- 易于切换 Provider

### 6. 异常处理
- 责任链中断时执行收尾节点
- 保证日志和通知能发出

---

## 总结

### 核心思想
- **责任链模式**：固定的 4 个节点，清晰的执行流程
- **策略模式**：支持多种调度策略，易于扩展
- **配置驱动**：模型分配通过配置控制
- **单一职责**：每个组件只做一件事

### 设计原则
- 责任链模式
- 策略模式
- Builder 模式
- 上下文对象模式
- 单一职责原则
- 开闭原则

### 执行流程
```
API → 异步执行 → 同步执行 → 责任链 → 4 个节点 → 业务调度 → 策略执行 → 构建 Agent/Task → 执行 Crew
```

### 模型分配
```
配置档位 → Strategy 读取 → CrewBuilder 解析 → 获取模型配置 → 创建 AIClient → 获取 LLM → 创建 Agent
```

### 扩展建议
- **新 Event**：继承 `BaseEvent` 并添加到链中
- **新 Strategy**：继承 `SchedulingStrategy` 并注册
- **新档位**：修改配置文件即可
