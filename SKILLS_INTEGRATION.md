# Skills 集成说明

## Skills 在 Crew 自动生成流程中的位置

### 完整流程

```
用户输入场景
    ↓
1. Topic 生成 (使用默认模型)
    ↓
2. Tasks 拆解 (使用默认模型)
    ↓
3. Agent 匹配/创建 (使用默认模型)
    ├─ 匹配现有 Agent
    │   └─ 如果匹配成功 → 使用现有 Agent（保留原有 Skills）
    │
    └─ 创建新 Agent
        ├─ 生成 Agent 配置 (role, goal, backstory)
        ├─ 🎯 AI 推荐 Skills (可选，失败不影响流程)
        │   ├─ 成功 → 为 Agent 配置推荐的 Skills
        │   ├─ 无推荐 → Agent 没有 Skills（正常）
        │   └─ 失败 → Agent 没有 Skills（正常）
        └─ 创建 Agent
    ↓
4. 模型分配 (使用默认模型，待实现)
    ↓
5. 创建 Crew
    ↓
6. 执行 Crew
    ├─ Agent 1 执行 Task 1
    │   ├─ 如果有 Skills → CrewAI 决定是否使用
    │   └─ 如果没有 Skills → 正常执行
    ├─ Agent 2 执行 Task 2
    └─ Agent 3 执行 Task 3
    ↓
7. 返回结果
```

## Skills 推荐的特点

### 1. **可选性**
- ✅ Skills 推荐是**可选的**，不是必需的
- ✅ 没有 Skills 的 Agent 可以正常工作
- ✅ Skills 推荐失败不会阻塞 Agent 创建

### 2. **自动化**
- ✅ AI 生成的 Agent 会**自动调用** Skills 推荐
- ✅ 手动创建的 Agent 可以选择是否推荐 Skills
- ✅ 推荐基于 Agent 的 role、goal、backstory 和任务上下文

### 3. **灵活性**
- ✅ Agent 可以有 0 个、1 个或多个 Skills
- ✅ CrewAI 在执行时**自主决定**是否使用 Skills
- ✅ Skills 不会被使用也是正常的（CrewAI 的行为）

## 代码实现

### Agent 创建流程（已优化）

```python
# crewai_web/web/services/agent_generator.py

async def create_agent(self, role_type: str, task_context: str) -> str:
    # 1. 生成 Agent 配置
    agent_config = await self.ai_client.call_structured(
        prompt=prompt,
        response_model=AgentConfig,
        role=role_type
    )
    
    # 2. AI 推荐 Skills（可选，失败不影响 Agent 创建）
    skills_config = None
    try:
        skills_recommender = get_skills_recommender()
        skills_config_dict = await skills_recommender.recommend_for_agent(
            role=agent_config.role,
            goal=agent_config.goal,
            backstory=agent_config.backstory,
            task_context=task_context
        )
        
        # 只有推荐了 Skills 才配置
        if skills_config_dict and skills_config_dict.get("preferred"):
            skills_config = SkillsConfig(**skills_config_dict)
            logger.info(f"✅ AI recommended {len(skills_config_dict['preferred'])} skills")
        else:
            logger.info(f"ℹ️  No skills recommended (this is normal)")
    
    except Exception as e:
        logger.warning(f"⚠️  Skills recommendation failed: {e}")
        logger.info(f"ℹ️  Agent will be created without skills (this is normal)")
    
    # 3. 创建 Agent（有无 Skills 都可以）
    agent_data = AgentCreate(
        name=agent_name,
        role=agent_config.role,
        goal=agent_config.goal,
        backstory=agent_config.backstory,
        skills_config=skills_config  # 可能是 None
    )
    
    created_agent = agent_service.create_agent(agent_data)
    return created_agent.id
```

### Skills 推荐逻辑

```python
# crewai_web/web/services/skills_recommender.py

async def recommend_for_agent(
    self, 
    role: str, 
    goal: str, 
    backstory: str,
    task_context: str = ""
) -> Dict[str, Any]:
    # 1. 获取所有已启用的 Skills
    all_skills = self.skills_service.list_all_skills(enabled_only=True)
    
    if not all_skills:
        # 没有可用的 Skills，返回空配置
        return {
            "mode": "auto",
            "preferred": [],
            "auto_match": True
        }
    
    # 2. 构建 prompt
    prompt = self.ai_client.load_prompt(
        "generator/skills_recommendation.prompt",
        role=role,
        goal=goal,
        backstory=backstory,
        task_context_line=task_context_line,
        available_skills=skills_info
    )
    
    # 3. 调用 AI 获取推荐
    try:
        recommendation = await self.ai_client.call_structured(
            prompt=prompt,
            response_model=SkillsRecommendationResponse,
            role=role
        )
        
        # 4. 转换为配置格式
        skills_config = self._convert_to_config(recommendation)
        return skills_config
    
    except Exception as e:
        logger.error(f"Failed to get AI recommendation: {e}")
        # 降级：返回空配置
        return {
            "mode": "auto",
            "preferred": [],
            "auto_match": True
        }
```

## 日志示例

### 场景 1：成功推荐 Skills

```
INFO: Requesting AI to recommend skills for 产品经理
INFO: ✅ AI recommended 2 skills: ['product-design', 'market-research']
INFO: Created agent '产品经理' -> agent_uuid_1
```

### 场景 2：没有推荐 Skills（正常）

```
INFO: Requesting AI to recommend skills for 项目经理
INFO: ℹ️  No skills recommended for 项目经理 (this is normal)
INFO: Created agent '项目经理' -> agent_uuid_2
```

### 场景 3：推荐失败（正常）

```
INFO: Requesting AI to recommend skills for 架构师
WARNING: ⚠️  Skills recommendation failed for 架构师: Connection timeout
INFO: ℹ️  Agent will be created without skills (this is normal)
INFO: Created agent '架构师' -> agent_uuid_3
```

## Skills 使用场景

### 1. **有 Skills 且被使用**

```
Agent: 前端工程师
Skills: [frontend-tools, code-review]
Task: 开发登录页面

执行过程：
- CrewAI 检测到 Agent 有 Skills
- CrewAI 判断 frontend-tools 对任务有帮助
- CrewAI 调用 frontend-tools 的工具
- Agent 完成任务
```

### 2. **有 Skills 但未使用**

```
Agent: 产品经理
Skills: [market-research, user-interview]
Task: 撰写产品文档

执行过程：
- CrewAI 检测到 Agent 有 Skills
- CrewAI 判断这些 Skills 对撰写文档没有直接帮助
- CrewAI 不调用任何 Skill
- Agent 直接用 LLM 完成任务
```

### 3. **没有 Skills**

```
Agent: 文档整理专员
Skills: []
Task: 整理项目文档

执行过程：
- Agent 没有 Skills
- Agent 直接用 LLM 完成任务
- 正常工作
```

## 设计原则

### 1. **非侵入性**
- Skills 是增强功能，不是必需功能
- 没有 Skills 的 Agent 可以正常工作
- Skills 推荐失败不影响主流程

### 2. **智能化**
- AI 根据 Agent 的角色和任务自动推荐
- 只推荐相关的 Skills，避免过度配置
- 支持降级策略（推荐失败 → 空配置）

### 3. **可控性**
- 用户可以手动启用/禁用 Skills
- 用户可以手动为 Agent 添加/移除 Skills
- AI 推荐只是建议，不是强制

### 4. **透明性**
- 清晰的日志说明推荐结果
- 明确说明"没有 Skills 是正常的"
- 失败时提供友好的提示

## 与模型分配的关系

Skills 推荐和模型分配是**独立的两个维度**：

```
Agent 配置 = {
    role: "前端工程师",
    goal: "开发高质量的前端代码",
    backstory: "...",
    
    // 维度 1：Skills（工具能力）
    skills: ["frontend-tools", "code-review"],
    
    // 维度 2：模型等级（推理能力）
    llm_config: {
        model_tier: "standard"  // 根据任务复杂度分配
    }
}
```

### 组合示例

| Agent | Skills | 模型等级 | 说明 |
|-------|--------|---------|------|
| 前端工程师 | frontend-tools | standard | 有工具，常规推理 |
| 架构师 | 无 | advanced | 无工具，深度推理 |
| 数据分析师 | data-analysis | standard | 有工具，常规推理 |
| 文档专员 | 无 | basic | 无工具，简单任务 |

## 总结

### ✅ 已实现
1. AI 生成 Agent 时自动推荐 Skills
2. Skills 推荐失败不影响 Agent 创建
3. 没有 Skills 是正常的（明确日志）
4. Skills 可能不被使用（CrewAI 决定）

### 🎯 核心理念
- **Skills 是可选的增强功能**
- **没有 Skills 的 Agent 可以正常工作**
- **CrewAI 自主决定是否使用 Skills**

### 📝 最佳实践
1. 不要强制要求 Agent 必须有 Skills
2. Skills 推荐失败时优雅降级
3. 记录清晰的日志，说明推荐结果
4. 允许用户手动调整 Skills 配置

---

**更新时间**: 2026-04-25  
**状态**: 已优化，符合设计原则
