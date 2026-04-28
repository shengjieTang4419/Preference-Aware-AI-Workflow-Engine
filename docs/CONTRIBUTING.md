# 开发者贡献指南

本文档面向人类开发者，包含详细的编码规范、最佳实践和项目约定。

---

## 目录结构

```
crewai_web/
├── core/           # 核心功能（AI、LLM、Tools）
├── web/
│   ├── api/        # API 端点
│   ├── services/   # 业务逻辑
│   ├── domain/     # 数据模型
│   └── runner/     # Crew 执行引擎
├── prompts/        # AI Prompts
└── skills/         # Skills（可选）
```

---

## Python 编码规范

### 代码风格
- 遵循 PEP 8
- 使用 Black 格式化（行长 88）
- 使用 isort 排序导入

### 类型注解
所有函数必须有类型注解：

```python
from typing import Optional, List
import logging

async def process_data(
    items: List[str], 
    max_count: Optional[int] = None
) -> dict:
    """
    处理数据项列表。
    
    Args:
        items: 要处理的数据项
        max_count: 最大处理数量，None 表示全部处理
    
    Returns:
        处理结果字典
    """
    pass
```

### 文档字符串
- 使用 Google 风格的 docstring
- 所有公共函数/类必须有 docstring
- 包含参数说明、返回值、可能的异常

### 导入顺序
1. 标准库
2. 第三方库
3. 本地模块

每组按字母排序。

### 异步编程
- 优先使用 async/await
- 避免阻塞操作
- 使用 asyncio + aiohttp

---

## JavaScript/TypeScript 规范

### 代码风格
- 使用 Prettier + ESLint
- 优先使用 TypeScript，避免 `any`

### Vue 3 组件
- 使用 Composition API + `<script setup>`
- 组件名用 PascalCase
- 函数名用 camelCase

示例：
```vue
<script setup lang="ts">
import { ref, computed } from 'vue'

interface Props {
  title: string
  count?: number
}

const props = defineProps<Props>()
const localCount = ref(props.count || 0)

const displayText = computed(() => `${props.title}: ${localCount.value}`)
</script>
```

---

## 文件命名约定

- **Python 模块**: 小写 + 下划线（`agent_service.py`）
- **类名**: PascalCase（`AgentGenerator`）
- **常量**: 大写 + 下划线（`MAX_RETRIES`）
- **测试文件**: `test_<module_name>.py`

---

## 错误处理

### 必须捕获的场景
- 所有外部调用（API、文件 I/O）
- 数据库操作
- 用户输入处理

### 最佳实践
```python
import logging

logger = logging.getLogger(__name__)

try:
    result = await external_api_call()
except ValueError as e:
    logger.error(f"Invalid value: {e}", exc_info=True)
    raise
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    return default_value
```

- 使用具体的异常类型，避免裸 `except`
- 记录错误日志（使用 `logging` 模块）
- 考虑是否需要重新抛出异常

---

## 性能优化

### 避免常见陷阱
- ❌ 在循环中进行 I/O 操作
- ❌ 重复查询数据库（N+1 问题）
- ❌ 加载整个大文件到内存

### 推荐做法
- ✅ 使用生成器或流式处理大数据
- ✅ 批量查询数据库
- ✅ 使用缓存减少重复计算

---

## 安全规范

### 敏感信息管理
**禁止**硬编码 API Key、密码、Token：

```python
# ❌ 错误
API_KEY = "sk-1234567890abcdef"

# ✅ 正确
import os
API_KEY = os.getenv("DASHSCOPE_API_KEY")
```

### 输入验证
- 所有用户输入必须验证（使用 Pydantic）
- 文件路径必须检查是否在允许的目录内
- SQL 查询使用参数化，防止注入

```python
from pydantic import BaseModel, validator

class UserInput(BaseModel):
    name: str
    age: int
    
    @validator('age')
    def age_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('age must be positive')
        return v
```

---

## 注释和文档

### 何时添加注释
- ✅ **需要**: 复杂算法、业务逻辑、非显而易见的决策
- ❌ **不需要**: 显而易见的代码

```python
# ❌ 不必要的注释
i += 1  # 增加计数器

# ✅ 有价值的注释
# 使用二分查找优化性能，因为数据已排序
index = binary_search(sorted_data, target)
```

---

## 测试规范

### 测试覆盖
- 核心业务逻辑必须有单元测试
- API 端点需要集成测试
- 使用 pytest（Python）

### 测试文件命名
- 文件: `test_<module_name>.py`
- 函数: `test_<function_name>_<scenario>`

示例：
```python
# test_agent_service.py
import pytest
from crewai_web.web.services.agent_service import AgentService

def test_create_agent_success():
    service = AgentService()
    agent = service.create_agent(name="Test Agent", role="Developer")
    assert agent.name == "Test Agent"

def test_create_agent_invalid_name():
    service = AgentService()
    with pytest.raises(ValueError):
        service.create_agent(name="", role="Developer")
```

---

## 日志规范

### 日志级别
- `DEBUG`: 详细的调试信息
- `INFO`: 关键流程节点（如 "开始生成 Crew"）
- `WARNING`: 可恢复的异常情况
- `ERROR`: 错误但程序可继续
- `CRITICAL`: 严重错误，程序可能崩溃

### 日志格式
```python
logger.info(f"生成 Crew: topic={topic}, tasks={len(tasks)}")
logger.error(f"AI 调用失败: {e}", exc_info=True)
```

---

## 性能目标

- API 响应时间: < 200ms（非 AI 调用）
- AI 生成时间: < 30s（单个 Agent/Task）
- Crew 执行: 根据任务复杂度，无硬性限制
- 前端首屏加载: < 2s

---

## 依赖管理

### Python
- 使用 `uv` 管理依赖
- `pyproject.toml` 定义依赖
- 固定主版本号，允许小版本更新

```toml
[project.dependencies]
fastapi = "^0.104.0"
pydantic = "^2.5.0"
```

### JavaScript
- 使用 `npm`
- `package.json` 固定版本
- 定期更新依赖（每月检查）

---

## API 响应格式

### 成功响应
```json
{
  "data": {
    "id": "123",
    "name": "Example"
  }
}
```

### 错误响应
```json
{
  "error": "错误信息",
  "detail": {
    "field": "name",
    "reason": "不能为空"
  }
}
```

### 列表响应
```json
{
  "data": [...],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

---

## 代码审查清单

在提交代码前，确保：
- [ ] 代码通过 linter 检查（Black + isort + ESLint）
- [ ] 所有测试通过
- [ ] 添加了必要的文档和注释
- [ ] 没有硬编码的敏感信息
- [ ] 错误处理完善
- [ ] 日志记录合理
- [ ] 性能考虑（避免 N+1、大文件加载等）

---

## Git 提交规范

使用 Conventional Commits 格式：

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型
- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具链

### 示例
```
feat(agent): 添加 Agent 角色验证

- 添加 role 字段的 Pydantic 验证
- 限制 role 长度为 1-50 字符
- 添加单元测试

Closes #123
```

---

**最后更新**: 2026-04-21
**维护者**: 一人公司团队
