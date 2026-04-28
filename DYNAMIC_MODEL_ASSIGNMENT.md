# 动态模型分配系统设计

## 核心理念

### 两层 AI 调用架构

```
┌─────────────────────────────────────────────────────────────┐
│ 第一层：系统内置 AI（元操作）                                  │
│ 使用：默认模型（Standard）                                     │
├─────────────────────────────────────────────────────────────┤
│ - Topic 生成                                                 │
│ - Task 拆解                                                  │
│ - Agent 匹配/创建                                            │
│ - Skills 推荐                                                │
│ - Preferences 提案生成                                       │
│ - 模型分配决策 ← 新增                                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 第二层：Crew 执行 AI（实际工作）                               │
│ 使用：动态分配的模型（Basic/Standard/Advanced）                │
├─────────────────────────────────────────────────────────────┤
│ - Agent 1: 数据整理 → Basic 模型                             │
│ - Agent 2: 需求分析 → Standard 模型                          │
│ - Agent 3: 架构设计 → Advanced 模型                          │
└─────────────────────────────────────────────────────────────┘
```

## 实现方案

### 1. Prompt 文件结构

```
crewai_web/prompts/
├── generator/
│   ├── topic.prompt              # 生成项目主题
│   ├── tasks.prompt              # 拆解任务
│   ├── agent.prompt              # 创建 Agent
│   ├── agent_match.prompt        # 匹配 Agent
│   ├── skills_recommendation.prompt  # 推荐 Skills
│   └── model_assignment.prompt   # 🆕 模型分配（新增）
└── preferences/
    ├── evolution.prompt          # 🆕 偏好进化（提取）
    └── diff_summary.prompt       # 🆕 变更摘要（提取）
```

### 2. 模型分配流程

```python
# 在 Crew 创建后、执行前，调用模型分配器

async def create_and_assign_crew(scenario: str):
    # 1. 生成 Crew 配置（使用默认模型）
    crew_config = await ai_generator_service.generate_crew_from_scenario(scenario)
    
    # 2. 🆕 动态分配模型（使用默认模型做决策）
    model_assignments = await model_assigner.assign_models(
        crew_id=crew_config["crew_id"],
        agents=crew_config["agent_ids"],
        tasks=crew_config["task_ids"]
    )
    
    # 3. 更新 Agent 配置，指定模型等级
    for assignment in model_assignments["assignments"]:
        agent_service.update_agent_llm_config(
            agent_id=assignment["agent_id"],
            model_tier=assignment["assigned_model_tier"]  # basic/standard/advanced
        )
    
    # 4. 执行 Crew（每个 Agent 使用分配的模型）
    result = await crew_service.execute_crew(crew_config["crew_id"])
    
    return result
```

### 3. 模型分配逻辑

#### 输入
```json
{
  "crew_name": "AI 编程教育平台开发",
  "process_type": "sequential",
  "tasks": [
    {
      "name": "市场调研",
      "description": "分析竞品和用户需求",
      "expected_output": "市场调研报告",
      "role_type": "市场分析师"
    },
    {
      "name": "架构设计",
      "description": "设计系统架构和技术选型",
      "expected_output": "技术架构方案",
      "role_type": "架构师"
    },
    {
      "name": "文档整理",
      "description": "整理所有输出文档",
      "expected_output": "项目文档包",
      "role_type": "文档专员"
    }
  ],
  "agents": [
    {"id": "agent_1", "role": "市场分析师"},
    {"id": "agent_2", "role": "架构师"},
    {"id": "agent_3", "role": "文档专员"}
  ]
}
```

#### 输出
```json
{
  "assignments": [
    {
      "agent_id": "agent_1",
      "agent_role": "市场分析师",
      "assigned_model_tier": "standard",
      "reason": "需要分析能力，但不涉及复杂决策",
      "tasks": ["市场调研"],
      "task_complexity": "medium"
    },
    {
      "agent_id": "agent_2",
      "agent_role": "架构师",
      "assigned_model_tier": "advanced",
      "reason": "负责架构设计和技术选型，需要深度推理",
      "tasks": ["架构设计"],
      "task_complexity": "high"
    },
    {
      "agent_id": "agent_3",
      "agent_role": "文档专员",
      "assigned_model_tier": "basic",
      "reason": "主要是格式化和整理，结构化任务",
      "tasks": ["文档整理"],
      "task_complexity": "low"
    }
  ],
  "summary": {
    "total_agents": 3,
    "basic_count": 1,
    "standard_count": 1,
    "advanced_count": 1,
    "optimization_note": "实现成本与质量的平衡"
  }
}
```

### 4. Agent 模型配置

#### 数据库 Schema 扩展
```python
# domain/agent.py
class Agent(BaseModel):
    id: str
    role: str
    goal: str
    backstory: str
    llm_config: Optional[LLMConfig] = None  # 🆕 新增字段
    
class LLMConfig(BaseModel):
    """Agent 的 LLM 配置"""
    provider: str = "dashscope"  # 使用哪个 provider
    model_tier: str = "standard"  # basic/standard/advanced
    temperature: Optional[float] = None  # 可选，覆盖默认值
```

#### CrewAI 集成
```python
# 创建 Agent 时指定模型
from crewai_web.core.llm import get_llm_for_agent

def create_crewai_agent(agent: Agent) -> CrewAIAgent:
    # 根据 Agent 的 llm_config 获取对应的 LLM
    if agent.llm_config:
        llm = llm_factory.get_llm(
            provider=agent.llm_config.provider,
            model_tier=agent.llm_config.model_tier,  # 🆕 使用分配的模型等级
            temperature=agent.llm_config.temperature
        )
    else:
        llm = llm_factory.get_llm()  # 使用默认模型
    
    return CrewAIAgent(
        role=agent.role,
        goal=agent.goal,
        backstory=agent.backstory,
        llm=llm,
        skills=agent.skills
    )
```

### 5. LLMFactory 扩展

```python
# core/llm/factory.py

class LLMFactory:
    def get_llm(
        self, 
        agent_name: Optional[str] = None, 
        provider: Optional[str] = None, 
        model: Optional[str] = None,
        model_tier: Optional[str] = None,  # 🆕 新增参数
        **kwargs
    ) -> LLM:
        provider = provider or self.default_provider
        llm_provider = self.providers[provider]
        
        # 🆕 如果指定了 model_tier，从配置中获取对应的模型
        if model_tier:
            model = llm_provider.get_model_by_tier(model_tier)
        elif not model:
            model = llm_provider.get_default_model()
        
        return llm_provider.create_llm(model, **kwargs)
```

```python
# core/llm/dashscope_provider.py

class DashScopeProvider(BaseLLMProvider):
    def get_model_by_tier(self, tier: str) -> str:
        """根据模型等级获取模型名称"""
        from crewai_web.web.domain import LLMConfig
        
        config = LLMConfig.load()
        if not config.dashscope:
            return self.get_default_model()
        
        tier_config = {
            "basic": config.dashscope.basic,
            "standard": config.dashscope.standard,
            "advanced": config.dashscope.advanced
        }.get(tier)
        
        return tier_config.model if tier_config else self.get_default_model()
```

## 使用场景示例

### 场景 1：简单任务流

```
用户输入：整理我的会议记录

AI 分配：
- Agent 1 (文档整理) → Basic 模型
  理由：简单的格式化任务

成本：低
质量：足够
```

### 场景 2：复杂项目

```
用户输入：设计一个微服务架构的电商系统

AI 分配：
- Agent 1 (需求分析) → Standard 模型
  理由：需要分析能力，但不涉及架构决策
  
- Agent 2 (架构设计) → Advanced 模型
  理由：核心任务，需要深度推理和技术选型
  
- Agent 3 (代码生成) → Standard 模型
  理由：常规编码任务
  
- Agent 4 (文档整理) → Basic 模型
  理由：结构化输出

成本：优化
质量：关键任务保证
```

### 场景 3：数据分析流

```
用户输入：分析销售数据并生成报告

AI 分配：
- Agent 1 (数据清洗) → Basic 模型
  理由：简单的数据处理
  
- Agent 2 (数据分析) → Standard 模型
  理由：需要分析和洞察
  
- Agent 3 (报告撰写) → Standard 模型
  理由：需要组织和表达能力
  
- Agent 4 (可视化建议) → Advanced 模型
  理由：需要创意和设计思维

成本：平衡
质量：分析和创意环节加强
```

## 优势

### 1. 成本优化
- ✅ 简单任务使用 Basic 模型，降低成本
- ✅ 只在关键任务使用 Advanced 模型
- ✅ 自动化决策，避免过度配置

### 2. 质量保证
- ✅ 核心任务使用高级模型，保证质量
- ✅ 根据任务复杂度动态调整
- ✅ 避免"大材小用"或"小材大用"

### 3. 灵活性
- ✅ 支持用户手动覆盖 AI 的分配决策
- ✅ 支持为特定 Agent 固定模型等级
- ✅ 支持实时调整和优化

### 4. 可观测性
- ✅ 记录每次分配决策和理由
- ✅ 统计成本和质量指标
- ✅ 支持 A/B 测试不同分配策略

## 实现步骤

### Phase 1: 基础设施（已完成）
- ✅ 三级模型配置系统
- ✅ JSON 热更新支持
- ✅ Provider 模型等级支持

### Phase 2: 模型分配器（待实现）
- [ ] 创建 `ModelAssigner` 服务
- [ ] 实现 `model_assignment.prompt` 调用
- [ ] 扩展 Agent Schema，添加 `llm_config` 字段
- [ ] 更新 Agent 创建逻辑，支持模型等级

### Phase 3: 集成和优化（待实现）
- [ ] 在 Crew 创建流程中集成模型分配
- [ ] 添加模型分配的 API 接口
- [ ] 前端展示模型分配结果
- [ ] 支持用户手动调整

### Phase 4: 监控和优化（待实现）
- [ ] 记录模型使用统计
- [ ] 分析成本和质量关系
- [ ] 优化分配策略

## 配置示例

### .env 文件（保持不变）
```bash
# API Keys（敏感信息）
DASHSCOPE_API_KEY=sk-xxx
CLAUDE_API_KEY=sk-ant-xxx
```

### JSON 配置（运行时）
```json
{
  "default_provider": "dashscope",
  "dashscope": {
    "basic": {
      "model": "qwen-turbo",
      "temperature": 0.3,
      "is_default": false
    },
    "standard": {
      "model": "qwen-plus",
      "temperature": 0.7,
      "is_default": true
    },
    "advanced": {
      "model": "qwen-max",
      "temperature": 0.9,
      "is_default": false
    }
  }
}
```

### Agent 配置（数据库）
```json
{
  "id": "agent_uuid",
  "role": "架构师",
  "goal": "设计高可用的系统架构",
  "backstory": "...",
  "llm_config": {
    "provider": "dashscope",
    "model_tier": "advanced",
    "temperature": 0.9
  }
}
```

---

**设计时间**: 2026-04-25  
**核心理念**: 两层 AI 调用，动态模型分配，成本与质量平衡
