# LLM Client 架构设计

## 概述

本文档描述 LLM（Large Language Model）客户端的架构设计思想，解释**为什么要这样设计**，以及各个组件的**职责划分**。

**核心目标**：
- 统一 AI 交互入口
- 支持多 Provider（DashScope、Claude 等）
- 配置驱动，易于扩展
- 支持动态模型选择

---

## 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      应用层                                   │
│  - CrewBuilder（构建 Agent 和 Task）                         │
│  - DynamicCrewBuilder（动态加载配置）                        │
│  - 业务逻辑                                                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              AIClient（AI 交互的唯一入口）                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  场景1：固定调用                                      │   │
│  │  get_default() → 使用默认配置                        │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  场景2：动态调用                                      │   │
│  │  create(provider, model) → 自定义配置                │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  核心方法：call(prompt, response_model)                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   LLMFactory（内部）                          │
│  职责：创建 LLM 实例（不对外暴露）                             │
│  - 确定使用哪个 Provider                                      │
│  - 验证配置                                                   │
│  - 委托给 Provider 创建 LLM                                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  ProviderRegistry                            │
│  职责：管理所有 Provider 实例                                 │
│  - 注册 Provider（dashscope, claude, ...）                   │
│  - 提供 Provider 查询接口                                     │
│  - 维护默认 Provider                                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  BaseLLMProvider（抽象类）                    │
│  职责：定义 Provider 接口                                     │
│  - create_llm(model, **kwargs) → 创建指定模型                │
│  - get_default_llm(**kwargs) → 创建默认模型                  │
│  - validate_config() → 验证配置（API Key）                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              具体 Provider 实现                               │
│  ┌──────────────────┐         ┌────────────────────────┐   │
│  │ DashScopeProvider│         │  ClaudeProvider        │   │
│  │ (阿里通义千问)    │         │  (Anthropic Claude)    │   │
│  └──────────────────┘         └────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   工具层                                      │
│  ┌────────────────────┐    ┌─────────────────────────┐     │
│  │  config_loader     │    │  provider_utils         │     │
│  │  读取配置文件      │    │  参数解析工具           │     │
│  └────────────────────┘    └─────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

---

## 设计思想

### 1. 为什么需要分层？

**问题**：如果没有分层，业务代码会直接调用各个 Provider 的 API，导致：
- 代码耦合严重（切换 Provider 需要改动大量代码）
- 配置分散（每个地方都要处理 API Key、temperature 等）
- 难以统一管理（无法统一 Debug、监控、限流）

**解决方案**：分层架构
```
应用层 → AIClient → LLMFactory → Provider → 具体实现
```

**好处**：
- 应用层只需要知道 `AIClient`，不关心底层实现
- 切换 Provider 只需要修改配置文件
- 统一管理 Debug、Preferences、监控

---

### 2. 为什么 AIClient 是唯一入口？

**设计原则**：**Facade 模式**（门面模式）

**问题**：如果允许多个入口：
```
业务代码 → LLMFactory
业务代码 → Provider
业务代码 → 直接调用 API
```
会导致：
- 调用方式不统一
- 难以添加横切关注点（Debug、日志、监控）
- 难以控制 LLM 的创建和使用

**解决方案**：统一入口
```
所有业务代码 → AIClient（唯一入口）
```

**好处**：
- 统一的调用方式
- 统一的 Debug、日志、监控
- 统一的错误处理
- 易于添加新功能（如缓存、限流）

---

### 3. 为什么需要 LLMFactory？

**设计原则**：**Factory 模式**（工厂模式）

**职责**：
- 创建 LLM 实例（不是业务逻辑）
- 决策使用哪个 Provider
- 验证配置

**为什么不让 AIClient 直接创建 LLM？**
- **单一职责**：AIClient 负责 AI 交互，Factory 负责对象创建
- **易于测试**：可以 Mock Factory，测试 AIClient
- **易于扩展**：新增创建逻辑不影响 AIClient

---

### 4. 为什么需要 ProviderRegistry？

**设计原则**：**Registry 模式**（注册表模式）

**职责**：
- 管理所有 Provider 实例（单例）
- 提供 Provider 查询接口
- 维护默认 Provider

**为什么不让 Factory 直接管理 Provider？**
- **单一职责**：Registry 负责管理，Factory 负责创建
- **易于扩展**：新增 Provider 只需要注册，不需要修改 Factory
- **全局共享**：所有地方都可以查询 Provider 信息

---

### 5. 为什么需要 BaseLLMProvider？

**设计原则**：**Template Method 模式**（模板方法模式）

**职责**：
- 定义 Provider 接口（抽象方法）
- 提供通用逻辑（模板方法）

**为什么不让每个 Provider 独立实现？**
- **代码复用**：通用逻辑（如 `get_default_llm`）只写一次
- **统一接口**：所有 Provider 都有相同的方法
- **易于扩展**：新增 Provider 只需要实现 `create_llm`

**模板方法示例**：
```
get_default_llm():  ← 模板方法（通用逻辑）
  1. 从配置读取默认模型
  2. 解析 temperature
  3. 调用 create_llm()  ← 抽象方法（子类实现）
```

---

### 6. 为什么需要 config_loader？

**设计原则**：**配置驱动**

**职责**：
- 从配置文件读取 LLM 配置
- 提供配置查询接口
- 单例模式，全局共享

**为什么不硬编码配置？**
- **易于修改**：修改配置不需要改代码
- **环境隔离**：开发/测试/生产环境使用不同配置
- **易于扩展**：新增模型只需要修改配置文件

**配置文件示例**：
```json
{
  "default_provider": "dashscope",
  "dashscope": {
    "basic": {"model": "qwen3.5-plus", "temperature": 0.7},
    "standard": {"model": "qwen3.6-plus", "temperature": 0.7, "is_default": true},
    "advanced": {"model": "qwen3.6-max-preview", "temperature": 0.7}
  }
}
```

---

### 7. 为什么需要 provider_utils？

**设计原则**：**DRY（Don't Repeat Yourself）**

**职责**：
- 提供通用的参数解析工具
- 避免重复代码

**典型场景**：temperature 参数的三级优先级
```
优先级1：kwargs 中显式传入
优先级2：配置文件中的值
优先级3：默认值 0.7
```

**为什么不让每个 Provider 自己实现？**
- **代码复用**：逻辑只写一次
- **统一行为**：所有 Provider 的行为一致
- **易于维护**：修改逻辑只需要改一个地方

---

## 职责划分

### 应用层
- **职责**：业务逻辑
- **依赖**：只依赖 `AIClient`
- **不关心**：底层如何创建 LLM

### AIClient
- **职责**：AI 交互的唯一入口
- **提供**：`get_default()` 和 `create()` 两种创建方式
- **集成**：Debug、Preferences、错误处理
- **不关心**：LLM 如何创建

### LLMFactory
- **职责**：创建 LLM 实例
- **决策**：使用哪个 Provider
- **委托**：具体创建逻辑交给 Provider
- **不关心**：Provider 的内部实现

### ProviderRegistry
- **职责**：管理所有 Provider 实例
- **提供**：Provider 查询接口
- **维护**：默认 Provider
- **不关心**：Provider 如何创建 LLM

### BaseLLMProvider
- **职责**：定义 Provider 接口
- **提供**：通用逻辑（模板方法）
- **要求**：子类实现 `create_llm`
- **不关心**：具体的模型 API

### 具体 Provider（DashScopeProvider、ClaudeProvider）
- **职责**：实现具体的 LLM 创建逻辑
- **调用**：具体的模型 API
- **不关心**：上层如何使用

### config_loader
- **职责**：读取和查询配置
- **提供**：配置查询接口
- **不关心**：配置如何被使用

### provider_utils
- **职责**：提供通用工具函数
- **提供**：参数解析、参数设置
- **不关心**：工具如何被使用

---

## 设计原则总结

### 1. 单一职责原则（SRP）
- 每个类只做一件事
- `AIClient` 负责交互，`Factory` 负责创建，`Registry` 负责管理

### 2. 开闭原则（OCP）
- 对扩展开放：新增 Provider 不需要修改现有代码
- 对修改封闭：修改配置不需要改代码

### 3. 依赖倒置原则（DIP）
- 依赖抽象（`BaseLLMProvider`），不依赖具体实现
- 上层不依赖下层，都依赖抽象

### 4. 接口隔离原则（ISP）
- `AIClient` 只暴露必要的接口（`get_default`、`create`、`call`）
- 内部实现（`Factory`、`Registry`）不对外暴露

### 5. 配置驱动
- 所有模型配置集中在配置文件
- 修改配置不需要改代码

---

## 使用场景

### 场景1：固定调用（90% 的场景）
**需求**：使用默认配置，不需要特殊模型

**方式**：
```
AIClient.get_default()
```

**流程**：
```
AIClient.get_default()
  → LLMFactory.get_llm()
  → ProviderRegistry.default_provider
  → DashScopeProvider.get_default_llm()
  → 返回默认 LLM（qwen3.6-plus）
```

---

### 场景2：动态调用（10% 的场景）
**需求**：需要高级模型、特定 Provider、自定义参数

**方式**：
```
AIClient.create(provider="claude", model="claude-3-opus-20240229")
```

**流程**：
```
AIClient.create(provider, model)
  → LLMFactory.get_llm(provider, model)
  → ProviderRegistry.get_provider("claude")
  → ClaudeProvider.create_llm("claude-3-opus-20240229")
  → 返回自定义 LLM
```

---

### 场景3：CrewBuilder 中的动态模型选择
**需求**：不同 Agent 使用不同档位的模型

**方式**：
```
builder.build_agent(agent_config, inputs, model_tier="advanced")
```

**流程**：
```
build_agent(model_tier="advanced")
  → config_loader.get_model_config_by_default_provider("advanced")
  → 返回 {"model": "qwen3.6-max-preview", "temperature": 0.7}
  → AIClient.create(model="qwen3.6-max-preview")
  → 返回高级 LLM
```

---

## 扩展性

### 新增 Provider（3 步）

**步骤1**：创建 Provider 类
- 继承 `BaseLLMProvider`
- 实现 `create_llm` 方法

**步骤2**：注册到 `ProviderRegistry`
- 在 `_providers` 字典中添加

**步骤3**：添加配置
- 在 `llm_settings.json` 中添加配置
- 设置环境变量（API Key）

**无需修改**：
- ❌ 不需要修改 `AIClient`
- ❌ 不需要修改 `LLMFactory`
- ❌ 不需要修改业务代码

---

### 新增模型档位（1 步）

**步骤**：修改配置文件
```json
{
  "dashscope": {
    "ultra": {
      "model": "qwen3.6-ultra",
      "temperature": 0.7,
      "is_default": false
    }
  }
}
```

**无需修改**：
- ❌ 不需要修改任何代码

---

## 架构优势

### 1. 易于维护
- 职责清晰，每个类只做一件事
- 修改一个组件不影响其他组件

### 2. 易于扩展
- 新增 Provider 只需 3 步
- 新增模型档位只需修改配置

### 3. 易于测试
- 每个组件可以独立测试
- 可以 Mock 依赖

### 4. 易于理解
- 分层清晰，职责明确
- 遵循设计原则

### 5. 统一管理
- 统一的 AI 交互入口
- 统一的配置管理
- 统一的 Debug、日志、监控

---

## 总结

### 核心思想
- **分层架构**：应用层 → AIClient → Factory → Provider → 具体实现
- **统一入口**：AIClient 是唯一的 AI 交互入口
- **配置驱动**：所有模型配置集中管理
- **易于扩展**：新增 Provider 和模型档位非常简单

### 设计原则
- 单一职责
- 开闭原则
- 依赖倒置
- 接口隔离
- 配置驱动

### 使用建议
- **90% 场景**：使用 `AIClient.get_default()`
- **10% 场景**：使用 `AIClient.create(provider, model)`
- **CrewBuilder**：使用 `model_tier` 参数动态选择模型

### 扩展建议
- **新 Provider**：继承 `BaseLLMProvider` 并注册
- **新档位**：修改配置文件即可
