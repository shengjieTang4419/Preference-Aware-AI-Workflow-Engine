# 开发守则（Development Conventions）

> 项目组共同遵守的编码与架构规范。
> 新人入职先读此文档，Review 时以此为准。

---

## 一、架构原则

### 1. 职责分离（Single Responsibility）
- 每个模块只做一件事，每个函数只做一件事
- 三层分离：**API 层**（薄路由）→ **Service 层**（纯函数）→ **Domain 层**（数据模型）
- API 层不写业务逻辑，只做请求转发 + 异常转换
- Service 层不依赖 HTTP 概念（不 import FastAPI）

### 2. 组合 > 继承（Composition over Inheritance）
- 优先注入/委托，不继承
- 场景扩展用 Adapter 模式，不用继承链

### 3. 依赖稳定契约（Stable Contracts）
- 对外调用走 Controller API / 公开接口，不走内部 Facade
- 模块间通过 Pydantic 模型交互，不用裸 dict/Map
- **强类型 > Map**：领域对象用 DTO/VO，Map 仅用于产品原生格式

### 4. 不过度设计（No Over-Engineering）
- 删除未使用的功能，不预留"将来可能用到"的代码
- 先用最简单的方式跑通，有实际需求再抽象
- stream 仅用于简单 1-2 行逻辑，复杂逻辑用 for-loop

---

## 二、编码规范

### 分层约定

```
crewai_web/web/
├── api/           # 薄路由层：接收请求 → 调用 service → 返回响应
├── services/      # 业务逻辑层：纯函数模块，不依赖 HTTP
├── domain/        # 数据模型层：Pydantic BaseModel
├── config.py      # 集中配置：所有 os.getenv() 在此读取
└── database.py    # 数据库连接：从 config.py 导入配置
```

### 命名规范
- 全部 `snake_case`
- 私有函数用 `_` 前缀（如 `_hash_password`）
- 区域分隔线：`# ── xxx ──────`
- 中文 docstring

### 服务层模板

```python
import logging
from crewai_web.web.config import XXX_DIR
from crewai_web.web.domain.xxx import XxxCreate, XxxOut

logger = logging.getLogger(__name__)

def _xxx_path(xxx_id: str) -> Path:
    """私有辅助函数"""
    ...

def list_xxx() -> List[XxxOut]:
    """获取列表"""
    ...

def create_xxx(req: XxxCreate) -> XxxOut:
    """创建"""
    ...
    raise ValueError("xxx already exists")  # 业务错误抛 ValueError
```

### API 层模板

```python
from fastapi import APIRouter, HTTPException
from crewai_web.web.domain.xxx import XxxCreate, XxxOut
from crewai_web.web.services import xxx_service

router = APIRouter(prefix="/xxx", tags=["xxx"])

@router.post("", response_model=XxxOut, status_code=201)
def create_xxx(req: XxxCreate):
    """创建"""
    try:
        return xxx_service.create_xxx(req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### Domain 层模板

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class XxxBase(BaseModel):
    name: str = Field(..., description="名称")

class XxxCreate(XxxBase):
    pass

class XxxOut(XxxBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True
```

### 配置管理
- 所有配置集中在 `config.py`，通过 `os.getenv()` 读取
- 敏感信息放 `.env`，不出现在代码中（即使是默认值）
- `.env` 在 `main.py` 中 `load_dotenv()`，早于 app import

### 错误处理
- 业务错误抛 `ValueError`
- API 层捕获 `ValueError` 转 `HTTPException`
- 全局异常处理器在 `app.py` 中定义

---

## 三、开发流程

### Skeleton-First（骨架先行）
- 先写 stubs + TODO，跑通主流程
- 再逐步填充实现细节
- **内部先通再闭环**：跑通内部链路优先于外部集成

### Review 前置
- 先讨论设计，再动手写代码
- 复杂功能先出方案文档，Review 通过再实现

### 不要踩的坑
- 不要在代码中硬编码路径（用 config.py + 相对路径）
- 不要一上来就铺太多功能，先聚焦核心场景
- 不要忽略成本控制（外部 API 调用有成本）
- 不要忽略"人审"环节（AI 生成内容质量不可控）

---

## 四、前端规范

### 组件结构
- 页面组件放 `views/`，公共组件放 `components/`
- API 调用统一走 `api/index.ts`，不直接 axios
- 状态管理用 Pinia store

### 样式规范
- 使用 Element Plus 组件，保持风格统一
- 渐变背景 + 白色卡片的登录/注册风格
- 响应式布局，移动端适配

---

## 五、数据库规范

### 表设计
- 主键用 `SERIAL`（整数自增）或 `UUID`
- 必须有 `created_at` 时间戳
- 字段命名 `snake_case`
- 建表语句放在 `database.py` 的 `init_db()` 中

### 连接管理
- 使用 asyncpg 连接池（min_size=1, max_size=10）
- 配置从 `config.py` 导入
- 应用关闭时释放连接池
