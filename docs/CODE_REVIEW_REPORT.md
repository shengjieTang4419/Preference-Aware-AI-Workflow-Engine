# 代码审查报告

> 审查日期: 2026-05-23
> 审查范围: 创意工坊、会员系统、技能市场、认证模块（后端 + 前端）
> 审查标准: `docs/DEVELOPMENT_CONVENTIONS.md`

---

## 一、审查概览

| 维度 | 评分 | 说明 |
|------|------|------|
| 架构分层 | ✅ 优秀 | API → Service → Domain 三层清晰分离 |
| 命名规范 | ✅ 优秀 | snake_case、中文 docstring、区域分隔线均符合规范 |
| 错误处理 | ⚠️ 良好 | 业务错误正确使用 ValueError，但存在几处遗漏 |
| 类型安全 | ⚠️ 一般 | 部分类型标注不完整，有裸 dict 传递 |
| 安全性 | ❌ 需改进 | subprocess 调用、JWT 默认值、脚本执行存在风险 |
| 代码复用 | ⚠️ 一般 | 认证提取逻辑重复 4 次，已重构 |
| 前端规范 | ✅ 良好 | API 统一调用、Pinia store、响应式布局规范 |

---

## 二、已修复的问题（直接重构）

### 2.1 【Bug】auth_service.register_user 缺少 virtual_money 字段
- **文件**: `crewai_web/web/services/auth_service.py`
- **问题**: `register_user()` 的 SQL 查询只 SELECT 了 `id, username, email, created_at`，但响应中尝试读取 `user.get("virtual_money")`，永远返回 None → 被 or 0 兜底为 0。注册成功后前端拿不到正确的虚拟余额。
- **修复**: 在 RETURNING 子句中添加 `virtual_money`，并使用 `UserInfo` 模型替代裸 dict 构造响应。

### 2.2 【Bug】auth_service.login_user 硬编码 virtual_money 为 0
- **文件**: `crewai_web/web/services/auth_service.py`
- **问题**: `login_user()` 的 SQL 查询已正确 SELECT 了 `virtual_money`，但响应构造时硬编码 `"virtual_money": 0`，导致登录后前端显示的余额永远为 0。
- **修复**: 改为 `float(user["virtual_money"] or 0)`，从数据库读取实际值。

### 2.3 【规范】TokenResponse.user 使用裸 dict 而非 Pydantic 模型
- **文件**: `crewai_web/web/services/auth_service.py`
- **问题**: `domain/auth.py` 已定义 `UserInfo` 模型，但 `TokenResponse.user` 类型为 `dict`，违反"模块间通过 Pydantic 模型交互"的契约。
- **修复**: 注册响应改用 `UserInfo.model_dump()` 构造。登录响应因需携带 `virtual_money`（UserInfo 中无此字段），暂保留 dict 并记录为后续建议。

### 2.4 【规范】creation_service.update_creation_status 类型标注不完整
- **文件**: `crewai_web/web/services/creation_service.py`
- **问题**: 参数 `output_dir: str = None, output_files: list = None` 使用了裸类型 + None 默认值，应使用 `Optional[X]`。
- **修复**: 全部改为 `Optional[str] = None`, `Optional[list] = None` 等。

### 2.5 【阻塞】skills_market_service.install_skill 阻塞事件循环
- **文件**: `crewai_web/web/services/skills_market_service.py`
- **问题**: 在 async 函数中使用同步 `subprocess.run()`，会阻塞整个事件循环，导致其他请求在安装技能期间无法响应。
- **修复**: 改用 `asyncio.create_subprocess_exec()` + `asyncio.wait_for()`，保持异步非阻塞。

### 2.6 【重复】认证用户提取逻辑重复 4 次
- **文件**: `api/auth.py`, `api/creations.py`, `api/creativity.py`, `api/skills_market.py`, `api/membership.py`
- **问题**: `_get_current_user_id` / `_get_user_id` 函数在 5 个文件中重复实现，逻辑几乎相同。
- **修复**: 新建 `crewai_web/web/api/deps.py`，提供三个共享依赖函数：
  - `get_optional_user_id()` — 未登录返回 None
  - `get_required_user_id()` — 未登录抛 401
  - `get_current_user()` — 返回完整用户信息

### 2.7 【类型】前端 DiscoverSkill.installs 类型不匹配
- **文件**: `frontend/src/api/types.ts`
- **问题**: 类型定义 `installs: number`，但后端 fallback 数据返回 `"1.5M"` 字符串。
- **修复**: 改为 `installs: number | string`。

### 2.8 【规范】前端 API 拦截器生产环境 console.log
- **文件**: `frontend/src/api/index.ts`
- **问题**: 请求拦截器中的 `console.log` 在生产环境也会输出，泄露 API 调用路径。
- **修复**: 用 `import.meta.env.DEV` 包裹，仅开发环境输出。

### 2.9 【规范】Skills.vue 遗留调试 console.log
- **文件**: `frontend/src/views/Skills.vue`
- **问题**: `console.log('[Skills] discover result:', ...)` 是开发调试遗留。
- **修复**: 已删除。

### 2.10 【竞态】membership_service.install_scene 跨连接操作
- **文件**: `crewai_web/web/services/membership_service.py`
- **问题**: `install_scene()` 在一个连接中检查场景存在性，然后调用 `get_user_accessible_tiers()`（使用另一个连接）检查权限。两次查询之间存在微小的竞态窗口。
- **修复**: 在同一连接上下文内完成权限检查，避免跨连接竞态。

---

## 三、建议改进（未直接修改，需讨论）

### 3.1 【安全】JWT_SECRET 空默认值
- **文件**: `crewai_web/web/config.py`
- **问题**: `JWT_SECRET = os.getenv("JWT_SECRET", "")` 允许空字符串。虽然后续 `auth_service` 会检查并抛错，但应在应用启动时就快速失败。
- **建议**: 在 `config.py` 中添加启动校验，或在 `main.py` 的 `startup` 事件中检查必要配置项。

### 3.2 【安全】LLM 生成脚本的执行安全
- **文件**: `crewai_web/web/services/creativity/data_analysis_strategy.py`
- **问题**: LLM 生成的 Python 脚本通过 `subprocess.run()` 直接执行，仅靠超时控制。恶意或错误的 LLM 输出可能执行危险操作（文件删除、网络请求等）。
- **建议**:
  1. 限制脚本可访问的目录（chroot / 沙箱）
  2. 禁止危险内置函数（`__import__`, `eval`, `exec`）
  3. 使用 `RestrictedPython` 或 Docker 容器隔离执行

### 3.3 【安全】subprocess 调用中的参数注入
- **文件**: `crewai_web/web/services/skills_market_service.py`
- **问题**: `install_skill()` 中 `package` 参数直接传入 `npx skills add`。虽然使用了 `create_subprocess_exec`（非 shell 模式），但仍建议验证 package 格式。
- **建议**: 添加正则校验 `package` 参数格式，如 `^[a-zA-Z0-9@/\-_.]+$`。

### 3.4 【规范】datetime.utcnow() 已弃用
- **文件**: 多个 service 文件
- **问题**: Python 3.12+ 中 `datetime.utcnow()` 已标记为 deprecated，建议使用 `datetime.now(timezone.utc)`。
- **建议**: 全局替换，当前不影响功能。

### 3.5 【架构】database.py 中 DDL 与种子数据混合
- **文件**: `crewai_web/web/database.py`
- **问题**: `init_db()` 既包含建表语句（DDL），又包含默认数据插入（DML）。场景配置的 8 条默认数据硬编码在代码中。
- **建议**:
  1. 将种子数据抽到 `seeds/` 目录下的 JSON/SQL 文件
  2. 或创建独立的 `seed_db()` 函数，与 `init_db()` 分离

### 3.6 【架构】scene_service 与 scene_config_service 功能重叠
- **文件**: `crewai_web/web/services/scene_service.py`, `crewai_web/web/api/scenes.py`
- **问题**: `scene_service.list_scenes()` 实际读取的是 `scene_configs` 表，与 `scene_config_service.list_configs()` 高度重叠。`scenes` API 路由和 `scene-configs` API 路由返回的数据源相同。
- **建议**: 评估是否可以合并，或明确区分两个服务的职责边界。

### 3.7 【安全】scene_config_service.update_config 动态 SQL 构造
- **文件**: `crewai_web/web/services/scene_config_service.py`
- **问题**: `update_config()` 使用 f-string 构造 SET 子句。虽然字段名来自 Pydantic 模型（已验证），但仍属于动态 SQL 拼接。
- **建议**: 当前风险较低（字段名由模型约束），可添加白名单校验作为额外防护。

### 3.8 【规范】config.py 硬编码 /tmp 路径
- **文件**: `crewai_web/web/config.py`
- **问题**: `ALLOWED_BROWSE_ROOTS` 中包含 `Path("/tmp")`，在非 Unix 系统上不可用。
- **建议**: 使用 `tempfile.gettempdir()` 替代。

### 3.9 【前端】Home.vue 使用 sceneConfigs API 但类型为 SceneConfig
- **文件**: `frontend/src/views/Home.vue`
- **问题**: Home 页面调用 `api.sceneConfigs.list()` 获取场景列表，但模板中访问了 `scene.price_tier`、`scene.exec_mode` 等 `SceneConfig` 特有字段。这意味着 `/scenes` API（返回 `SceneOut`，无这些字段）实际上不会被 Home 页面使用。
- **建议**: 确认 `SceneOut` 是否仍有存在必要，避免维护两套相似模型。

### 3.10 【规范】全局异常处理缺失
- **文件**: 无（应存在于 `app.py`）
- **问题**: 当前各 API 路由分别捕获 `ValueError`，但未捕获的异常（如数据库连接失败）会返回 500 原始错误，可能泄露内部信息。
- **建议**: 在 `app.py` 中添加全局异常处理器，捕获未处理的异常并返回通用错误信息。

---

## 四、文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `crewai_web/web/api/deps.py` | 新建 | 共享认证依赖 |
| `crewai_web/web/api/auth.py` | 重构 | 使用共享依赖 |
| `crewai_web/web/api/creations.py` | 重构 | 使用共享依赖 |
| `crewai_web/web/api/creativity.py` | 重构 | 使用共享依赖 |
| `crewai_web/web/api/skills_market.py` | 重构 | 使用共享依赖 |
| `crewai_web/web/api/membership.py` | 重构 | 使用共享依赖 |
| `crewai_web/web/services/auth_service.py` | 修复 | virtual_money bug + UserInfo 模型 |
| `crewai_web/web/services/creation_service.py` | 修复 | Optional 类型标注 |
| `crewai_web/web/services/membership_service.py` | 修复 | 竞态条件 |
| `crewai_web/web/services/skills_market_service.py` | 修复 | 异步 subprocess |
| `frontend/src/api/types.ts` | 修复 | DiscoverSkill.installs 类型 |
| `frontend/src/api/index.ts` | 修复 | 生产环境 console.log |
| `frontend/src/views/Skills.vue` | 修复 | 移除调试日志 |

---

## 五、总结

本次审查覆盖了约 30 个新增文件，整体代码质量良好，架构分层清晰，命名规范一致。发现并修复了 **2 个数据正确性 Bug**（virtual_money 字段遗漏）、**1 个阻塞性能问题**（同步 subprocess）、**5 处代码重复**（认证依赖提取）、以及若干规范性问题。

安全性方面有 3 项需要重点关注：LLM 生成脚本的沙箱执行、JWT 配置的启动校验、subprocess 参数验证。建议在下一迭代中优先处理。
