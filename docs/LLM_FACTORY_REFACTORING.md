# LLM Factory 重构文档

## 概述

将原有的 `llm_factory.py` 重构为更加模块化和可扩展的架构，支持多个 LLM 提供商，并提供前端配置界面。

## 架构变更

### 旧架构
```
crewai_web/core/llm_factory.py  # 单文件包含所有逻辑
```

### 新架构
```
crewai_web/core/llm/
├── __init__.py              # 模块导出
├── base_provider.py         # 抽象基类
├── dashscope_provider.py    # 通义千问实现
├── claude_provider.py       # Claude 实现（预留）
└── factory.py              # 工厂类
```

## 核心组件

### 1. BaseLLMProvider (抽象基类)

定义了所有 LLM 提供商必须实现的接口：

- `create_llm(model, **kwargs)` - 创建 LLM 实例
- `validate_config()` - 验证配置是否完整
- `get_provider_name()` - 获取提供商名称
- `get_available_models()` - 获取可用模型列表
- `get_default_model()` - 获取默认模型

### 2. DashScopeProvider

通义千问（阿里云百炼）的实现：

**环境变量：**
- `DASHSCOPE_API_KEY` - API 密钥（必需）
- `DASHSCOPE_BASE_URL` - API 基础 URL（可选）
- `DASHSCOPE_DEFAULT_MODEL` - 默认模型（可选）
- `DASHSCOPE_TEMPERATURE` - 温度参数（可选）

**可用模型：**
- qwen-max, qwen-max-latest
- qwen-plus, qwen-plus-latest
- qwen-turbo, qwen-turbo-latest
- qwen2.5-72b-instruct, qwen2.5-32b-instruct
- qwen2.5-14b-instruct, qwen2.5-7b-instruct

### 3. ClaudeProvider

Claude (Anthropic) 的实现（预留）：

**环境变量：**
- `CLAUDE_API_KEY` - API 密钥（必需）
- `CLAUDE_BASE_URL` - API 基础 URL（可选）
- `CLAUDE_DEFAULT_MODEL` - 默认模型（可选）
- `CLAUDE_TEMPERATURE` - 温度参数（可选）

**可用模型：**
- claude-3-5-sonnet-20241022
- claude-3-5-haiku-20241022
- claude-3-opus-20240229
- claude-3-sonnet-20240229
- claude-3-haiku-20240307

### 4. LLMFactory

工厂类，负责管理和创建 LLM 实例：

**方法：**
- `get_llm(agent_name, provider, model, **kwargs)` - 获取 LLM 实例
- `get_provider(provider_name)` - 获取提供商实例
- `list_providers()` - 列出所有提供商及其状态

**便捷函数：**
- `get_llm_for_agent(agent_name, **kwargs)` - 为指定 Agent 获取 LLM
- `get_default_llm(**kwargs)` - 获取默认 LLM

## API 端点

新增 `/api/llm` 路由组：

### GET /llm/providers
列出所有可用的 LLM 提供商及其配置状态

**响应：**
```json
{
  "providers": [
    {
      "name": "dashscope",
      "display_name": "Dashscope",
      "is_configured": true,
      "available_models": ["qwen-max", "qwen-plus", ...],
      "default_model": "qwen-plus-latest"
    }
  ],
  "default_provider": "dashscope"
}
```

### GET /llm/settings
获取当前 LLM 设置（API Key 已脱敏）

**响应：**
```json
{
  "default_provider": "dashscope",
  "dashscope": {
    "api_key": "sk-a...xyz",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "default_model": "qwen-plus-latest",
    "temperature": 0.7
  },
  "claude": { ... }
}
```

### PUT /llm/settings
更新 LLM 设置并保存到 .env 文件

**请求体：**
```json
{
  "default_provider": "dashscope",
  "dashscope": {
    "api_key": "sk-...",
    "base_url": "https://...",
    "default_model": "qwen-plus-latest",
    "temperature": 0.7
  }
}
```

### POST /llm/test/{provider}
测试指定提供商的连接

**参数：**
- `provider` - 提供商名称 (dashscope | claude)
- `model` - 可选，测试的模型名称

## 前端界面

新增 `/llm-settings` 页面，提供可视化配置界面：

**功能：**
- 选择默认 LLM 提供商
- 配置各提供商的 API Key、Base URL、默认模型、Temperature
- 实时显示配置状态（已配置/未配置）
- 测试连接功能
- 保存配置到 .env 文件

**路由：**
- 路径：`/llm-settings`
- 组件：`LLMSettings.vue`
- 导航：侧边栏 "LLM 设置" 菜单项

## 环境变量配置

更新了 `.env.example`，新增完整的 LLM 配置示例：

```env
# 默认 LLM 提供商
DEFAULT_LLM_PROVIDER=dashscope

# DashScope 配置
DASHSCOPE_API_KEY=your_api_key
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
DASHSCOPE_DEFAULT_MODEL=qwen-plus-latest
DASHSCOPE_TEMPERATURE=0.7

# Claude 配置
CLAUDE_API_KEY=your_api_key
CLAUDE_BASE_URL=https://api.anthropic.com/v1
CLAUDE_DEFAULT_MODEL=claude-3-5-sonnet-20241022
CLAUDE_TEMPERATURE=0.7

# Agent 专属配置（可选）
AGENT_CEO_LLM=dashscope:qwen-max-latest
AGENT_TECH_LEAD_LLM=claude:claude-3-5-sonnet-20241022
```

## 迁移指南

### 代码迁移

旧的导入：
```python
from crewai_web.core.llm_factory import LLMFactory
```

新的导入：
```python
from crewai_web.core.llm import LLMFactory
```

### 使用方式

使用方式保持不变，向后兼容：

```python
# 获取默认 LLM
llm = llm_factory.get_llm()

# 为特定 Agent 获取 LLM
llm = llm_factory.get_llm(agent_name="ceo")

# 指定提供商和模型
llm = llm_factory.get_llm(provider="claude", model="claude-3-5-sonnet-20241022")
```

## 扩展新提供商

要添加新的 LLM 提供商：

1. 创建新的提供商类继承 `BaseLLMProvider`
2. 实现所有抽象方法
3. 在 `factory.py` 中注册提供商
4. 更新前端类型定义和 UI

示例：

```python
# crewai_web/core/llm/openai_provider.py
from .base_provider import BaseLLMProvider

class OpenAIProvider(BaseLLMProvider):
    def create_llm(self, model: str, **kwargs):
        # 实现逻辑
        pass
    
    # ... 实现其他方法
```

```python
# crewai_web/core/llm/factory.py
from .openai_provider import OpenAIProvider

class LLMFactory:
    def __init__(self):
        self.providers = {
            "dashscope": DashScopeProvider(),
            "claude": ClaudeProvider(),
            "openai": OpenAIProvider(),  # 新增
        }
```

## 优势

1. **模块化设计** - 每个提供商独立实现，易于维护
2. **可扩展性** - 通过继承基类轻松添加新提供商
3. **配置管理** - 前端可视化配置，自动保存到 .env
4. **类型安全** - 完整的 TypeScript 类型定义
5. **向后兼容** - 保持原有 API 接口不变
6. **测试友好** - 提供连接测试功能

## 注意事项

1. 修改配置后需要重启应用才能生效
2. API Key 在前端显示时会自动脱敏
3. .env 文件更新是原子性的，不会丢失其他配置
4. Claude 提供商目前为预留实现，需要根据实际 API 调整
