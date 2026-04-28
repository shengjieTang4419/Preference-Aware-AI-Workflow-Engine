# 偏好系统设计文档

## 核心理念

**一个人 = 一个世界观**

不管做什么任务（生成 Java 代码、Python 代码、做计划、做分析），沉淀的都是"我"对世界的理解和偏好。

---

## 文件结构

```
.crew/
├── system_rules.md       # 静态：Agent 系统规则（手动维护）
└── preferences.md        # 动态：个人世界观和偏好（自动进化）

docs/
└── CONTRIBUTING.md       # 静态：编码规范（给人看）
```

---

## 完整流程

### 1. Agent 执行时

```python
# 调用 loader.load()
system_prompt = system_rules.md + preferences.md

# 注入到 Agent 的 system prompt
agent = Agent(
    role="Python 开发者",
    backstory=system_prompt,  # 包含系统规则 + 个人偏好
    ...
)
```

**结果**：Agent 遵循系统规则（如安全准则、输出格式）和个人偏好（如优先可读性、简洁文档）

---

### 2. Crew 执行完成后

```python
# 异步触发进化服务
async def on_crew_complete(exec_id, execution_result):
    # 只读取偏好文件（不包含系统规则）
    original_preferences = loader.load_preferences_only()
    
    # LLM 分析执行效果
    new_preferences = llm.analyze(
        original_preferences=original_preferences,
        execution_result=execution_result
    )
    
    # 生成提案（类似 Git PR）
    proposal = create_proposal(
        original=original_preferences,
        suggested=new_preferences
    )
    
    # 用户审核后，只更新 preferences.md
    if user_approve(proposal):
        save_to_file(".crew/preferences.md", new_preferences)
```

**结果**：只更新个人偏好，不修改系统规则

---

### 3. 闭环

```
下次 Agent 执行时 → 读取更新后的 preferences.md → 遵循新的偏好 → 形成正反馈循环
```

**越用越顺手！**

---

## 关键代码

### PreferencesLoader

```python
class PreferencesLoader:
    def load(self) -> str:
        """Agent 执行时调用：加载系统规则 + 个人偏好"""
        return system_rules.md + preferences.md
    
    def load_preferences_only(self) -> str:
        """进化服务调用：只加载个人偏好"""
        return preferences.md
```

### 使用示例

```python
# Agent 执行
loader = get_preferences()
full_prompt = loader.load()  # 系统规则 + 偏好

# 进化服务
preferences_only = loader.load_preferences_only()  # 只有偏好
```

---

## 未来优化方向

### 1. 偏好整理
定期清理冗余和过时的偏好

### 2. 偏好坍缩
合并相似的偏好条目

### 3. 置信度提升
根据使用频率调整置信度

### 4. 用户隔离
商业化后支持多用户独立偏好

---

**版本**: 1.0  
**最后更新**: 2026-04-21
