# 创意工坊 — AI Creative Workshop

### 一个想法进来，任意形态的成果出去。

[![Python 3.13+](https://img.shields.io/badge/Python-3.13%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Vue 3](https://img.shields.io/badge/Vue-3-42b883?logo=vuedotjs)](https://vuejs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql)](https://postgresql.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **ChatGPT 给你答案，创意工坊给你可用的成品。**
>
> 输入：一句话 / 一段描述 / 一个想法
> 输出：文档 / 数据报告 / PPT / Excel / 代码 / 音乐 / 视频 / 游戏

---

## 项目定位

```
AI 聊天工具（ChatGPT / Claude）
  → 给你答案（文字）

创意工坊（本项目）
  → 给你成品（文件）
  → 输入想法 → AI 自动编排多个 Agent → 产出可用的制品
```

---

## 核心功能

### 🎨 创意工坊（首页）

场景卡片式交互，用户选择场景后输入想法，AI 自动产出制品。

```
┌─────────────────────────────────────────────────────┐
│  🎨 创意工坊 — 一个想法，无限可能                      │
│                                                       │
│  [  输入你的想法...  ] [📎上传] [开始创造]              │
│                                                       │
│  🔥 热门场景                                           │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐        │
│  │ 📝     │ │ 📊     │ │ 🎨     │ │ 💻     │        │
│  │结构化   │ │数据    │ │产品    │ │写代码   │        │
│  │文档     │ │分析    │ │PPT     │ │        │        │
│  │免费·自动│ │免费·自动│ │基础·人工│ │免费·自动│        │
│  └────────┘ └────────┘ └────────┘ └────────┘        │
└─────────────────────────────────────────────────────┘
```

### 🏪 模版市场

模版的"应用商店"。用户浏览、安装、使用场景模版。

- 已安装的模版显示在创意工坊首页
- 未安装的模版需要"安装"或"升级解锁"
- 支持分类筛选（文档 / 数据 / 代码 / 多媒体）
- 支持阶梯收费（免费 / 基础 / 高级）

### ⭐ 会员体系

三档会员，阶梯式权益：

| 等级 | 价格 | 可用场景 | 特权 |
|------|------|---------|------|
| Free | 免费 | 仅免费场景 | 基础功能 |
| Pro | ¥29.9/月 | 免费 + 基础场景 | 无限创作 · 优先排队 |
| Max | ¥99.9/月 | 全部场景 | 含音乐/视频 · 专属客服 · API 额度加倍 |

- 激活码兑换（PRO-3M-XXXXX 格式）
- 虚拟金额系统（分享裂变 / 发布模版赚取）
- 充值流水记录

### 🔧 技能发现与管理

集成 [skills.sh](https://skills.sh/) 技能排行榜，一键安装：

- 热门技能展示（来自 skills.sh Top 排行）
- 一键安装 → AI 自动生成结构化说明
- 已安装技能管理（查看说明 / 卸载）

### 📤 创作产出（策略模式）

基于策略模式的制品生成引擎，每种输出类型一个策略：

```
用户输入 → LLM 生成内容 → 策略处理 → 输出文件

DocumentStrategy      → Markdown → .md 文件
DataAnalysisStrategy  → Python 脚本 → 执行 → 图表 + 报告
PPTStrategy           → 幻灯片大纲 → python-pptx → .pptx
ExcelStrategy         → 数据结构 → openpyxl → .xlsx
CodeStrategy          → 代码文件 → zip 打包
GameStrategy          → HTML5 代码 → .html（浏览器直接运行）
MusicStrategy         → 音乐描述 → Suno API → .mp3
VideoStrategy         → 视频脚本 → Kling API → .mp4
```

新增输出类型只需：**新建一个策略文件 + 注册到 STRATEGY_MAP**，不改任何已有代码。

### 🧠 偏好进化

Agent 越用越懂你。每次执行后自动分析结果，提议偏好更新：

```
执行 → 分析 → 提议 → 用户审批 → 偏好更新 → 下次执行自动应用
```

---

## 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Vue 3)                         │
│  创意工坊 · 模版市场 · 会员中心 · 技能管理 · 执行历史        │
└─────────────────────────────┬───────────────────────────────┘
                              │ REST / WebSocket
┌─────────────────────────────▼───────────────────────────────┐
│                     FastAPI 服务层                            │
│                                                              │
│  ┌────────────┐  ┌────────────┐  ┌──────────────────────┐  │
│  │ 创作引擎    │  │ 场景管理    │  │ 用户/会员/技能       │  │
│  │ (策略模式)  │  │ (配置驱动)  │  │ (认证/权限/流水)     │  │
│  └────────────┘  └────────────┘  └──────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  CrewAI 编排层（Pipeline + 责任链）                    │   │
│  │  偏好进化 · 模型路由 · WebSocket 实时推送              │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│  PostgreSQL + pgvector  │  LLM 层 (DashScope / Claude)      │
│  用户 · 会员 · 场景 · 创作记录 · 流水                       │
└─────────────────────────────────────────────────────────────┘
```

**设计模式：**
- 策略模式（Strategy）— 创作输出类型可插拔
- 责任链模式（Chain of Responsibility）— Crew 执行流程
- Pipeline 模式 — Crew 生成 7 步工作流
- 适配器模式（Adapter）— 场景扩展点

---

## 快速开始

```bash
# 1. 克隆
git clone <repo-url>
cd one_person_company

# 2. 配置
cp .env.example .env
# 编辑 .env，设置 API Key 和数据库密码

# 3. 启动数据库（Docker）
cd ~/Documents/docker
docker compose up -d cloud-pgvector

# 4. 启动后端
make backend   # → http://localhost:8000

# 5. 启动前端
make frontend  # → http://localhost:5173

# 6. 使用
# 浏览器打开 → 注册账号 → 进入创意工坊 → 选择场景 → 输入想法 → 开始创造
```

---

## 项目结构

```
crewai_web/
├── core/
│   ├── ai/              # LLM 客户端（AIClient）
│   ├── llm/             # Provider 实现（DashScope, Claude）
│   ├── event/           # 事件框架
│   ├── chain/           # 责任链执行引擎
│   └── tools/           # WebSocket 管理器, Skills 加载器
├── web/
│   ├── api/             # FastAPI 路由（REST）
│   ├── services/        # 业务逻辑层（纯函数）
│   │   ├── creativity/  # 创作策略引擎
│   │   │   ├── strategy.py           # 策略基类
│   │   │   ├── document_strategy.py   # 文档策略
│   │   │   └── data_analysis_strategy.py # 数据分析策略
│   │   ├── auth_service.py            # 认证服务
│   │   ├── membership_service.py      # 会员服务
│   │   ├── skills_market_service.py   # 技能市场服务
│   │   └── ...
│   ├── domain/          # Pydantic 数据模型
│   ├── config.py        # 集中配置
│   └── database.py      # 数据库连接 + 建表
└── prompts/             # LLM 提示词模板

frontend/src/
├── api/                 # API 客户端（REST）
├── stores/              # Pinia 状态管理
├── views/
│   ├── Home.vue         # 创意工坊首页
│   ├── TemplateMarket.vue # 模版市场
│   ├── Membership.vue   # 会员中心
│   ├── Skills.vue       # 技能发现与管理
│   ├── Login.vue        # 登录
│   └── Register.vue     # 注册
└── router/              # Vue Router

docs/
├── DEVELOPMENT_CONVENTIONS.md  # 开发守则
├── CREW_GENERATION_ARCHITECTURE.md
├── CREW_EXECUTION_ARCHITECTURE.md
└── ...
```

---

## 技术栈

| 层 | 技术 |
|---|------|
| **前端** | Vue 3 + TypeScript + Element Plus + Pinia |
| **后端** | FastAPI + Pydantic v2 + Uvicorn |
| **数据库** | PostgreSQL 17 + pgvector（向量检索预留） |
| **ORM** | asyncpg（连接池） |
| **认证** | JWT（bcrypt + PyJWT） |
| **Agent 编排** | CrewAI |
| **LLM** | DashScope（Qwen）, Claude, OpenRouter |
| **Python** | 3.13+, uv 包管理 |
| **容器** | Docker Compose |

---

## 开发守则

详见 [docs/DEVELOPMENT_CONVENTIONS.md](docs/DEVELOPMENT_CONVENTIONS.md)

核心原则：
- **职责分离** — API（薄路由）→ Service（纯函数）→ Domain（数据模型）
- **组合 > 继承** — 策略模式 / 适配器模式，不继承链
- **不过度设计** — 先跑通，有需求再抽象
- **契约先行** — 模块间通过 Pydantic 模型交互

---

## Roadmap

### Phase 1 ✅ 已完成
- [x] 创意工坊首页（场景卡片 + 文件上传）
- [x] 模版市场（浏览 / 安装 / 分类筛选）
- [x] 会员体系（Free / Pro / Max / 激活码 / 流水）
- [x] 用户认证（注册 / 登录 / JWT）
- [x] 技能发现与管理（skills.sh 集成 / AI 说明）
- [x] 结构化文档策略（Markdown 输出）
- [x] 数据分析策略（Python 脚本执行 + 图表）
- [x] PostgreSQL + pgvector 数据库

### Phase 2 进行中
- [ ] PPT 生成策略（python-pptx）
- [ ] Excel 图表策略（openpyxl）
- [ ] 代码项目策略（多文件 + zip 打包）
- [ ] 创作历史详情页（制品预览 + 下载）
- [ ] 前端对接创作执行 API

### Phase 3 计划中
- [ ] 小游戏策略（HTML5 代码生成）
- [ ] 图片生成策略（通义万相 / DALL-E）
- [ ] 用户发布模版到市场
- [ ] 虚拟金额赚取（分享裂变）

### Phase 4 远期
- [ ] 音乐生成策略（Suno API）
- [ ] 视频生成策略（Kling API）
- [ ] 偏好进化 2.0（规则标签 / 置信度 / 冲突检测）
- [ ] 多租户 / 团队协作

---

## 许可证

MIT License — 开源免费，可商用。
