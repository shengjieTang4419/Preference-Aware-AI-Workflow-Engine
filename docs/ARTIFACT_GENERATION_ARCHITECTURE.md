# 制品生成架构 — Skills 驱动

> 版本: v1.0 | 日期: 2026-06-01 | 状态: Phase 1-3 完成

## 1. 核心思想

**Skills 是通用积木，Crew 是执行引擎，制品生成只是 Crew 最后一个节点。**

```
用户输入 → 魔法棒匹配Skills → Crew Pipeline(8步) → 最后一步执行artifact skills → 制品
```

## 2. 架构总览

```
┌──────────────────────────────────────────────────────────────┐
│                        前端 (Vue 3)                           │
│  首页场景卡片 → 输入 → 魔法棒 → 确认 → 等待 → 展示制品         │
└──────────────┬───────────────────────────────────┬───────────┘
               │ POST /api/magic-wand/match        │ POST /api/executions
               ▼                                    ▼
┌──────────────────────┐    ┌──────────────────────────────────────┐
│  MagicWandService    │    │  CrewGenerationPipeline (8步)         │
│  匹配artifact skills │    │                                      │
│  优先级:              │    │  1. GenerateTopicEvent                │
│  1. 预配置            │    │  2. GenerateTasksPlanEvent             │
│  2. 本地扫描          │    │  3. MatchAgentsEvent                   │
│  3. installed.json    │    │  4. CreateCrewEvent                    │
│  4. 场景推断          │    │  5. CreateTasksEvent                   │
└──────────────────────┘    │  6. AssignModelsEvent                  │
                             │  7. VerifyEvent                        │
                             │  8. ExecuteArtifactEvent  ← NEW        │
                             │       │                                  │
                             │       ▼                                  │
                             │  SkillChain.execute()                   │
                             │       │                                  │
                             │       ▼                                  │
                             │  SkillExecutor.execute()                │
                             │  (per skill: llm_script/subprocess)     │
                             └──────────────────────────────────────┘
```

## 3. 数据库设计

### 3.1 修改表: scene_configs

```sql
-- 新增字段
ALTER TABLE scene_configs ADD COLUMN artifact_skills JSONB DEFAULT '[]';
```

Pydantic 域模型增加 `field_validator` 兼容字符串/JSON 两种存储格式:

```python
class SceneConfigBase(BaseModel):
    artifact_skills: List[str] = Field(default_factory=list)

    @field_validator("artifact_skills", mode="before")
    @classmethod
    def parse_artifact_skills(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else []
        return v or []
```

默认数据:
| scene_id | artifact_skills |
|----------|----------------|
| document | ["documentation-writer"] |
| data-analysis | ["excel-automation"] |
| ppt | ["pptx"] |
| excel | ["excel-automation"] |
| code | ["code-generator"] |

### 3.2 新增表: artifact_skill_executions

```sql
CREATE TABLE artifact_skill_executions (
    id SERIAL PRIMARY KEY,
    execution_id VARCHAR(100) NOT NULL,   -- 关联到 creative_artifacts.execution_id
    skill_name VARCHAR(100) NOT NULL,     -- 哪个 skill
    step_index INT NOT NULL DEFAULT 0,    -- 链路中第几步 (0-based)
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending/running/completed/failed
    input_summary TEXT,                   -- 输入摘要 (前500字符, 调试用)
    output_files TEXT[],                  -- 产出文件路径列表
    output_metadata JSONB DEFAULT '{}',   -- 产出元数据
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.3 修改表: creative_artifacts

```sql
ALTER TABLE creative_artifacts ADD COLUMN skill_chain JSONB DEFAULT '[]';
ALTER TABLE creative_artifacts ADD COLUMN crew_execution_id VARCHAR(100);
```

## 4. 文件清单

### 新增 (7个)

| 文件 | 职责 | 关键类/函数 |
|------|------|-------------|
| `web/domain/artifact.py` | 制品领域模型 | `SkillResult`, `ArtifactResult`, `ArtifactSkillExecOut` |
| `web/services/skill_executor.py` | 单Skill执行器 | `SkillExecutor.execute()` |
| `web/services/skill_chain.py` | 多Skill链路编排 | `SkillChain.execute()` |
| `web/services/magic_wand_service.py` | 魔法棒匹配 | `match_artifact_skills()` |
| `web/services/artifact_execution_service.py` | 执行记录CRUD | `create_exec_record()`, `update_exec_record()` |
| `web/api/magic_wand.py` | 魔法棒API | `POST /api/magic-wand/match` |
| `web/events/execute_artifact_event.py` | Pipeline第8步 | `ExecuteArtifactEvent.do_execute()` |

### 修改 (10个)

| 文件 | 改动 |
|------|------|
| `web/database.py` | `artifact_skill_executions` 建表 + `scene_configs`/`creative_artifacts` 加字段 |
| `web/domain/scene_config.py` | `artifact_skills` 字段 + `field_validator` |
| `web/services/scene_config_service.py` | INSERT 语句加入 `artifact_skills` |
| `web/services/skills/skill_metadata_parser.py` | 解析 `type`/`output_type`/`execution`/`input_requires` |
| `web/events/__init__.py` | 导出 `ExecuteArtifactEvent` |
| `web/events/*.py` (7个) | `total` 从 7 改为 8 |
| `web/api/__init__.py` | 注册 `magic_wand_router` |
| `core/event/event_context.py` | 新增 `artifact_skills`/`crew_output`/`artifact_result` |
| `.vscode/launch.json` | 无改动 (已恢复) |

### 删除 (8个)

| 文件 | 原因 |
|------|------|
| `web/services/creativity/strategy.py` | 被 `skill_executor.py` 替代 |
| `web/services/creativity/ppt_strategy.py` | 被 `pptx` skill 替代 |
| `web/services/creativity/document_strategy.py` | 被 `documentation-writer` skill 替代 |
| `web/services/creativity/data_analysis_strategy.py` | 被 `excel-automation` skill 替代 |
| `web/services/creativity/__init__.py` | 策略注册中心, 不再需要 |
| `web/services/creativity_service.py` | 被 Pipeline + skill_chain 替代 |
| `web/domain/creativity.py` | 被 `domain/artifact.py` 替代 |
| `web/api/creativity.py` | 被 `magic_wand.py` + Crew Pipeline 替代 |

## 5. 核心模块设计

### 5.1 SkillExecutor — 单Skill执行

```
输入: skill_name + input_data + execution_id
输出: SkillResult (success, output_text, output_files)

执行模式 (从SKILL.md metadata.execution.mode读取):
  llm_script (默认): LLM根据SKILL.md生成脚本 → 执行脚本
    - 自动检测runtime: node / python
    - node: 生成.js → node执行 → .pptx/.docx等
    - python: 生成.py → python执行 → .png/.md等
  subprocess: 直接执行skill自带的 scripts/ 目录
  api_call: 调外部API (TODO)

Skill搜索路径 (按优先级):
  1. storage/skills/installed.json (已安装)
  2. ~/.agents/skills/ (全局安装)
  3. ~/.hermes/skills/ (Hermes skills)
  4. 项目内 skills/ 目录
```

### 5.2 SkillChain — 多Skill链路编排

```
输入: skill_names[] + crew_output + execution_id
输出: ArtifactResult (skill_chain, success, output_files)

执行逻辑:
  for i, skill in enumerate(skill_names):
      1. 创建 artifact_skill_executions 记录 (status=running)
      2. 调用 SkillExecutor.execute()
      3. 更新记录 (status=completed/failed)
      4. 下一个skill的输入 = 当前skill的文本输出
      5. 如果失败, 链路中断, 返回错误

  第一个skill: 接收 crew_output + context_files + ocr_texts
  后续skill: 只接收前一个的 output_text
```

### 5.3 MagicWandService — Skills匹配

```
输入: scene_id + user_input + scene_artifact_skills
输出: List[Dict] (matched skills with name/output_type/description)

四级匹配:
  1. scene_configs.artifact_skills (预配置, 最高优先级)
  2. 扫描本地SKILL.md, type=artifact的
  3. installed.json中名称包含artifact关键词的
  4. 根据scene_id推断 (ppt→pptx, document→documentation-writer等)
```

### 5.4 ExecuteArtifactEvent — Pipeline第8步

```
EventContext 输入:
  scenario: 用户场景描述
  execution_id: 执行ID
  crew_output: Crew执行的文本输出 (如果有的话)

执行逻辑:
  1. 从 scene_config 读取 artifact_skills
  2. 调用 match_artifact_skills() 匹配 (可能覆盖预配置)
  3. 如果有匹配到的skills, 调用 SkillChain.execute()
  4. 结果写入 ctx.artifact_result

EventContext 输出:
  artifact_skills: ["pptx"]  -- 匹配到的skills
  artifact_result: {         -- 制品结果
      skill_chain, success, title, description,
      output_type, output_files, preview_text
  }
```

## 6. API 接口

### POST /api/magic-wand/match

```json
// Request
{
    "scene_id": "ppt",
    "user_input": "帮我做一个产品介绍PPT"
}

// Response
{
    "scene_id": "ppt",
    "skills": [
        {"name": "pptx", "output_type": "pptx", "description": ""}
    ],
    "source": "preset"  // preset | scanned | inferred
}
```

## 7. Skill 元数据规范 (SKILL.md frontmatter)

```yaml
---
name: pptx
description: 专业PPT演示文稿生成

# 制品类型标识
type: artifact              # tool (Agent工具) | artifact (制品生成)

# 制品相关 (type=artifact时有效)
output_type: pptx           # pptx | docx | xlsx | md | mp4 | mp3 | pdf
input_requires:             # 需要什么输入
  - text
  - files

# 执行配置
execution:
  mode: llm_script          # llm_script | subprocess | api_call
  runtime: node             # node | python | auto (自动检测)
  entrypoint: generate.js   # subprocess模式的入口脚本
---
```

## 8. 待实现 (Phase 4)

- [ ] 前端魔法棒交互: 点击 → 调 /api/magic-wand/match → 显示匹配的skills → 确认后走Pipeline
- [ ] 前端清理: 移除旧 creativity API 引用 (frontend/src/api/index.ts, Home.vue)
- [ ] Crew输出衔接: Crew Runner 执行完后, 将输出写入 ctx.crou_output
- [ ] 制品结果持久化: artifact_result 写入 creative_artifacts 表
- [ ] 用户发布场景: 用户自定义 scene_configs.artifact_skills
