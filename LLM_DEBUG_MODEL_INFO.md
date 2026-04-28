# LLM 调试日志 - 模型信息

## 新增功能

在 LLM 调试日志中添加了模型信息，方便追踪每次调用使用的是哪个模型。

## 修改内容

### 1. AIClient 保存模型信息

`@/workspaces/one_person_company/crewai_web/core/ai/client.py:42-44`

```python
# 保存模型信息（用于日志）
self.llm_key = llm_key
self.model_name = getattr(self.llm, 'model', 'unknown')
```

### 2. 初始化时输出模型信息

```python
if debug_enabled:
    logger.info(f"🐛 LLM Debug enabled, logs will be saved to: {debug_dir or '.local/llm_debug'}")
    logger.info(f"📊 Using model: {self.model_name}")
```

### 3. 调用时传递模型信息

```python
# 在 call() 方法中
self.debug.log_prompt(full_prompt, role=role, model=self.model_name)
self.debug.log_response(response, elapsed=elapsed, role=role, model=self.model_name)

# 在 call_text() 方法中
self.debug.log_prompt(full_prompt, role=role, model=self.model_name)
self.debug.log_response(response, elapsed=elapsed, role=role, model=self.model_name)
```

### 4. DebugService 记录模型信息

#### 控制台日志

```python
# Prompt 日志
self.logger.info(f"{role_prefix}LLM Prompt (trace_id={trace_id} model={model}):\n{prompt[:200]}...")

# Response 日志
self.logger.info(
    f"{role_prefix}LLM Response (trace_id={trace_id}, elapsed={elapsed:.2f}s model={model}):\n{response[:200]}..."
)
```

#### 文件日志

**Prompt 文件**（`prompt_xxx.txt`）：
```markdown
# Model: qwen-plus
# Trace ID: 20260426-125030_123
# Role: 前端工程师

# Role: 你是一个 AI Agent Skills 推荐专家
...
```

**Response 文件**（`response_xxx.txt`）：
```markdown
# Model: qwen-plus
# Trace ID: 20260426-125031_456
# Role: 前端工程师
# Elapsed: 1.23s

{
  "recommended_skills": [...]
}
```

## 使用示例

### 启用调试

在 `.env` 文件中：
```bash
LLM_DEBUG_ENABLED=true
```

### 控制台输出

```bash
INFO: 🐛 LLM Debug enabled, logs will be saved to: .local/llm_debug
INFO: 📊 Using model: qwen-plus
INFO: [前端工程师] LLM Prompt (trace_id=20260426-125030_123 model=qwen-plus):
# Role: 你是一个 AI Agent Skills 推荐专家...

INFO: [前端工程师] LLM Response (trace_id=20260426-125031_456, elapsed=1.23s model=qwen-plus):
{
  "recommended_skills": [...]
}
```

### 文件输出

```bash
# 查看 prompt 文件
cat .local/llm_debug/prompt_20260426-125030_123.txt

# 输出：
# Model: qwen-plus
# Trace ID: 20260426-125030_123
# Role: 前端工程师

# Role: 你是一个 AI Agent Skills 推荐专家
...
```

```bash
# 查看 response 文件
cat .local/llm_debug/response_20260426-125031_456.txt

# 输出：
# Model: qwen-plus
# Trace ID: 20260426-125031_456
# Role: 前端工程师
# Elapsed: 1.23s

{
  "recommended_skills": [...]
}
```

## 使用场景

### 场景 1：对比不同模型的效果

```bash
# 使用 qwen-plus（默认）
curl -X POST http://localhost:8000/api/skills/ai-recommend \
  -d '{"role": "前端工程师", "goal": "开发前端代码"}'

# 查看日志
grep "Model:" .local/llm_debug/prompt_*.txt | tail -1
# 输出：# Model: qwen-plus

# 修改配置使用 qwen-max
# 再次调用 API

# 查看日志
grep "Model:" .local/llm_debug/prompt_*.txt | tail -1
# 输出：# Model: qwen-max
```

### 场景 2：追踪模型切换

```bash
# 查看最近 10 次调用使用的模型
grep "Model:" .local/llm_debug/prompt_*.txt | tail -10

# 输出：
# Model: qwen-plus
# Model: qwen-plus
# Model: qwen-max
# Model: qwen-plus
# Model: claude-sonnet-4.6
...
```

### 场景 3：统计模型使用情况

```bash
# 统计每个模型的使用次数
grep "Model:" .local/llm_debug/prompt_*.txt | cut -d' ' -f3 | sort | uniq -c

# 输出：
#  15 qwen-plus
#   3 qwen-max
#   2 claude-sonnet-4.6
```

### 场景 4：查找特定模型的调用

```bash
# 查找所有使用 qwen-max 的调用
grep -l "Model: qwen-max" .local/llm_debug/prompt_*.txt

# 输出：
# .local/llm_debug/prompt_20260426-125030_123.txt
# .local/llm_debug/prompt_20260426-130045_789.txt
```

## 日志格式

### Prompt 文件格式

```markdown
# Model: <模型名称>
# Trace ID: <追踪ID>
# Role: <角色名称>

<实际的 prompt 内容>
```

### Response 文件格式

```markdown
# Model: <模型名称>
# Trace ID: <追踪ID>
# Role: <角色名称>
# Elapsed: <耗时>s

<实际的 response 内容>
```

### 控制台日志格式

```
INFO: [<角色>] LLM Prompt (trace_id=<ID> model=<模型>):
<prompt 前 200 字符>...

INFO: [<角色>] LLM Response (trace_id=<ID>, elapsed=<耗时>s model=<模型>):
<response 前 200 字符>...
```

## 模型信息来源

```python
# AIClient 初始化时获取模型信息
self.llm = self.llm_factory.get_llm(llm_key)
self.model_name = getattr(self.llm, 'model', 'unknown')
```

CrewAI 的 `LLM` 对象有一个 `model` 属性，包含模型名称：
- DashScope: `qwen-plus`, `qwen-max`, `qwen-turbo`
- Claude: `claude-sonnet-4.6`, `claude-opus-4`, `claude-haiku-4`

## 优势

### 1. 可追溯性

- ✅ 每次调用都记录了使用的模型
- ✅ 可以追踪模型切换的历史
- ✅ 方便定位问题（某个模型的输出质量）

### 2. 对比分析

- ✅ 对比不同模型的输出质量
- ✅ 对比不同模型的响应时间
- ✅ 评估模型的成本效益

### 3. 调试便利

- ✅ 快速定位使用了错误的模型
- ✅ 验证模型分配是否正确
- ✅ 检查模型配置是否生效

### 4. 统计分析

- ✅ 统计每个模型的使用频率
- ✅ 分析模型的平均响应时间
- ✅ 评估模型的成本分布

## 示例输出

### 完整的调试日志

```bash
# 启动后端
INFO: 🐛 LLM Debug enabled, logs will be saved to: .local/llm_debug
INFO: 📊 Using model: qwen-plus

# 调用 Skills 推荐 API
INFO: [前端工程师] LLM Prompt (trace_id=20260426-125030_123 model=qwen-plus):
# Role: 你是一个 AI Agent Skills 推荐专家

# Task
为以下 Agent 推荐最合适的 Skills：

**Agent 信息**：
- 角色：前端工程师
- 目标：开发高质量的前端代码
...

INFO: [前端工程师] LLM Response (trace_id=20260426-125031_456, elapsed=1.23s model=qwen-plus):
{
  "recommended_skills": [
    {
      "skill_name": "frontend-tools",
      "reason": "前端工程师必备的工具和规范",
      "priority": "high"
    }
  ],
  "mode": "hybrid"
}
```

### Prompt 文件内容

```bash
cat .local/llm_debug/prompt_20260426-125030_123.txt
```

```markdown
# Model: qwen-plus
# Trace ID: 20260426-125030_123
# Role: 前端工程师

# Role: 你是一个 AI Agent Skills 推荐专家

# Task
为以下 Agent 推荐最合适的 Skills：

**Agent 信息**：
- 角色：前端工程师
- 目标：开发高质量的前端代码
- 背景：我是一位资深前端工程师
- 任务上下文：开发电商网站

**可用的 Skills**：
- frontend-tools: 前端开发工具和规范
- backend-tools: 后端开发工具和规范

# Requirements
1. **精准匹配**：推荐与 Agent 角色和目标最相关的 Skills
...
```

### Response 文件内容

```bash
cat .local/llm_debug/response_20260426-125031_456.txt
```

```markdown
# Model: qwen-plus
# Trace ID: 20260426-125031_456
# Role: 前端工程师
# Elapsed: 1.23s

{
  "recommended_skills": [
    {
      "skill_name": "frontend-tools",
      "reason": "前端工程师必备的工具和规范",
      "priority": "high"
    }
  ],
  "mode": "hybrid"
}
```

## 总结

### 新增内容

1. ✅ AIClient 保存模型信息
2. ✅ 初始化时输出模型信息
3. ✅ 控制台日志包含模型信息
4. ✅ 文件日志包含模型信息（文件开头）

### 日志格式

- **控制台**：`[角色] LLM Prompt (trace_id=xxx model=xxx)`
- **文件**：文件开头添加元数据（Model, Trace ID, Role, Elapsed）

### 使用场景

- ✅ 追踪模型使用历史
- ✅ 对比不同模型效果
- ✅ 统计模型使用情况
- ✅ 调试模型配置问题

---

**更新时间**: 2026-04-26  
**核心改进**: 在调试日志中添加模型信息，方便追踪和分析
