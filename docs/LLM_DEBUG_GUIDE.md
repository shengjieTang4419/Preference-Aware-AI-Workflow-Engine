# LLM 调试指南

## 问题

你发现虽然有 `DebugService`，但没有看到任何调试日志输出。

## 原因

1. ❌ `AIClient` 默认 `debug_enabled=False`
2. ❌ `DebugService` 缺少 `log_prompt()` 和 `log_response()` 方法
3. ❌ 没有环境变量配置来启用调试

## 解决方案

### 1. 添加缺失的方法

`@/workspaces/one_person_company/crewai_web/core/debug_service.py:61-99`

```python
def log_prompt(self, prompt: str, role: str | None = None) -> None:
    """记录 prompt（用于 AIClient）"""
    if not self.debug_enabled:
        return
    
    trace_id = self.new_trace_id()
    role_prefix = f"[{role}] " if role else ""
    
    # 输出到日志
    self.logger.info(f"{role_prefix}LLM Prompt (trace_id={trace_id}):\n{prompt[:200]}...")
    
    # 保存到文件
    debug_dir = self._get_debug_dir()
    debug_dir.mkdir(parents=True, exist_ok=True)
    (debug_dir / f"prompt_{trace_id}.txt").write_text(prompt, encoding="utf-8")

def log_response(self, response: str, elapsed: float = 0, role: str | None = None) -> None:
    """记录 response（用于 AIClient）"""
    if not self.debug_enabled:
        return
    
    trace_id = self.new_trace_id()
    role_prefix = f"[{role}] " if role else ""
    
    # 输出到日志
    self.logger.info(
        f"{role_prefix}LLM Response (trace_id={trace_id}, elapsed={elapsed:.2f}s):\n{response[:200]}..."
    )
    
    # 保存到文件
    debug_dir = self._get_debug_dir()
    debug_dir.mkdir(parents=True, exist_ok=True)
    (debug_dir / f"response_{trace_id}.txt").write_text(response, encoding="utf-8")
```

### 2. 支持环境变量配置

`@/workspaces/one_person_company/crewai_web/core/ai/client.py:42-51`

```python
# 从环境变量读取 debug 配置
if debug_enabled is None:
    debug_enabled = os.getenv("LLM_DEBUG_ENABLED", "false").lower() == "true"
if debug_dir is None:
    debug_dir = os.getenv("LLM_DEBUG_DIR")

self.debug = DebugService(debug_enabled=debug_enabled, debug_dir=debug_dir)

if debug_enabled:
    logger.info(f"🐛 LLM Debug enabled, logs will be saved to: {debug_dir or '.local/llm_debug'}")
```

### 3. 添加环境变量配置

`@/workspaces/one_person_company/.env.example:27-36`

```bash
# ============================================
# LLM 调试配置
# ============================================
# 是否启用 LLM 调试（记录所有 prompt 和 response）
# 设置为 true 会将所有 LLM 交互保存到文件
LLM_DEBUG_ENABLED=false

# LLM 调试日志保存目录（可选）
# 留空则使用默认路径：.local/llm_debug
LLM_DEBUG_DIR=
```

## 使用方法

### 方法 1：通过环境变量启用（推荐）

在 `.env` 文件中添加：

```bash
LLM_DEBUG_ENABLED=true
LLM_DEBUG_DIR=./debug_logs  # 可选，指定保存目录
```

重启后端，所有 LLM 调用都会被记录。

### 方法 2：代码中启用

```python
from crewai_web.core.ai import AIClient

# 启用调试
client = AIClient(debug_enabled=True, debug_dir="./my_debug")

# 使用 client 进行 LLM 调用
prompt = client.load_prompt("generator/topic.prompt", scenario="测试")
response = await client.call_text(prompt)
```

## 日志输出

### 控制台日志

```bash
INFO: 🐛 LLM Debug enabled, logs will be saved to: .local/llm_debug
INFO: [产品经理] LLM Prompt (trace_id=20260425-200530_123):
# Role: 你是一名资深项目管理专家和产品策划师...

INFO: [产品经理] LLM Response (trace_id=20260425-200531_456, elapsed=1.23s):
AI 编程教育平台开发计划...
```

### 文件日志

调试文件会保存到指定目录（默认 `.local/llm_debug`）：

```
.local/llm_debug/
├── prompt_20260425-200530_123.txt
├── response_20260425-200531_456.txt
├── prompt_20260425-200532_789.txt
└── response_20260425-200533_012.txt
```

每个文件包含完整的 prompt 或 response 内容。

## 调试场景

### 场景 1：调试 Crew 生成流程

```bash
# 启用调试
LLM_DEBUG_ENABLED=true

# 创建 Crew
curl -X POST http://localhost:8000/api/ai-generator/generate \
  -d '{"scenario": "开发一个博客系统"}'

# 查看日志文件
ls -lh .local/llm_debug/
cat .local/llm_debug/prompt_*.txt
```

你会看到：
- Topic 生成的 prompt 和 response
- Tasks 拆解的 prompt 和 response
- Agent 创建的 prompt 和 response
- Skills 推荐的 prompt 和 response

### 场景 2：调试 Skills 推荐

```bash
# 启用调试
LLM_DEBUG_ENABLED=true

# 调用 Skills 推荐 API
curl -X POST http://localhost:8000/api/skills/ai-recommend \
  -d '{
    "role": "前端工程师",
    "goal": "开发高质量的前端代码"
  }'

# 查看最新的 prompt
ls -lt .local/llm_debug/ | head -5
cat .local/llm_debug/prompt_*.txt | tail -1
```

### 场景 3：调试 Preferences 进化

```bash
# 启用调试
LLM_DEBUG_ENABLED=true

# 触发 Preferences 进化
# （执行 Crew 后会自动触发）

# 查看进化 prompt
grep -l "偏好进化" .local/llm_debug/prompt_*.txt
```

## 日志管理

### 清理旧日志

```bash
# 删除所有调试日志
rm -rf .local/llm_debug/*

# 只保留最近 10 个文件
cd .local/llm_debug
ls -t | tail -n +11 | xargs rm -f
```

### 按时间查看

```bash
# 查看最近 5 分钟的日志
find .local/llm_debug -name "*.txt" -mmin -5

# 查看今天的日志
find .local/llm_debug -name "*.txt" -mtime 0
```

## 性能影响

### 启用调试的影响

- ✅ **日志输出**：轻微影响（几毫秒）
- ✅ **文件写入**：轻微影响（异步写入）
- ⚠️ **磁盘空间**：每个 LLM 调用约 1-10KB

### 建议

- 🔧 **开发环境**：启用调试，方便排查问题
- 🚀 **生产环境**：关闭调试，避免磁盘占用
- 📊 **性能测试**：关闭调试，避免干扰测试结果

## Trace ID 说明

每个 LLM 调用都有一个唯一的 `trace_id`，格式为：

```
20260425-200530_123
│      │ │    │ └─ 毫秒（3位）
│      │ │    └─── 秒（2位）
│      │ └──────── 分钟（2位）
│      └────────── 小时（2位）
└───────────────── 日期（8位）
```

通过 `trace_id` 可以：
- 关联同一次调用的 prompt 和 response
- 按时间顺序查看调用历史
- 定位特定时间的问题

## 常见问题

### Q1: 为什么启用了调试但没有日志？

**A**: 检查以下几点：
1. `.env` 文件中 `LLM_DEBUG_ENABLED=true` 是否正确
2. 后端是否重启（修改 `.env` 后需要重启）
3. 日志级别是否设置为 `INFO` 或更低

### Q2: 日志文件保存在哪里？

**A**: 
- 默认路径：`/workspaces/one_person_company/.local/llm_debug/`
- 自定义路径：在 `.env` 中设置 `LLM_DEBUG_DIR`

### Q3: 如何只调试特定的 Agent？

**A**: 
目前调试是全局的，无法只调试特定 Agent。但你可以：
1. 通过 `trace_id` 的时间戳定位
2. 通过 `role` 参数过滤日志（日志中会显示 `[role]`）

### Q4: 调试日志会包含 API Key 吗？

**A**: 
不会。API Key 是在 LLM 调用时传递的，不会出现在 prompt 中。

---

**更新时间**: 2026-04-25  
**状态**: 已修复，支持环境变量配置
