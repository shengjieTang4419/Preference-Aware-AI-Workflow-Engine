# Preference-Aware AI Workflow Engine

### An AI workflow engine that learns your preferences

[![Python 3.13+](https://img.shields.io/badge/Python-3.13%2B-blue.svg)](https://python.org)
[![CrewAI](https://img.shields.io/badge/Powered%20by-CrewAI-FF6B35?logo=crewai)](https://crewai.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **A single LLM call gives you an answer. This engine gives you an AI workflow that learns.**
>
> Not faster AI — AI that understands you better over time.

**English** | [中文](README_CN.md)

---

## What Problem Does This Solve

**AI code generation tools are getting stronger, but architecture design still relies on humans.**

Cursor, Windsurf, and Claude Code can write code for you, but they can't help you think through:

- How to decompose a system into modules and how those modules communicate
- Where the boundaries are — what to build vs. what to buy
- How to balance tech choices against cost and team capability

This project is not about AI writing code. It's about **AI-assisted architecture design**: input a business scenario, get structured architecture documentation + key code scaffolding, then take that to your IDE for efficient implementation.

---

## Core Capabilities

### 1. Preference Evolution — Agents That Learn Your Style

```
Input scenario → AI decomposes tasks → Agents collaborate → Results analyzed → Preferences auto-updated
```

After each Crew execution, the system analyzes results and automatically proposes updates to `.crew/preferences.md`. Once you approve, Agents understand your style from the next run onward.

```markdown
<!-- .crew/preferences.md — auto-evolving -->
## Coding Standards
- Readability first, conciseness second
- Type annotations required
- No pointless comments

## Output Style
- Get to the point, no fluff
- Code blocks must have language identifiers
```

**Why this matters:** A single LLM call can't do this. RAG can't do this. Context windows can't either. Preference Evolution requires a full closed loop: execute → analyze → propose → review → update.

### 2. Three-Tier Dynamic Model Assignment — Balancing Cost and Quality

Not every task needs the most powerful model.

```
Documentation cleanup  → Basic (qwen-turbo)      Lowest cost
General analysis       → Standard (qwen-plus)     Balanced
Architecture design    → Advanced (qwen-max)      Highest quality
```

AI automatically selects the model based on task complexity. You can also override manually.

### 3. Full Execution Observability

- **SSE real-time logs** — Watch Agents work step by step
- **Execution history** — Review any past run's complete record
- **Intermediate artifacts** — Each Task's output is independently viewable
- **LLM call traces** — Debug info includes model name + trace_id

---

## Use Cases

### Use Case 1: Architecture Design (Core Scenario)

```
Input: "Design a SaaS subscription management system with multi-tenancy, billing, and notifications"

System output:
├── System architecture diagram
├── Module breakdown + responsibility boundaries
├── Core interface definitions
├── Technology recommendations
├── Key code scaffolding (not full implementation — architecture skeleton)
└── Implementation roadmap
```

Engineers take this document and implement the details in their IDE of choice.

### Use Case 2: Parallel Task Acceleration

```
Input: "Analyze competitors, finalize tech stack, write project documentation"
→ Agent 1 (Competitor Analysis) + Agent 2 (Tech Selection) + Agent 3 (Documentation) run in parallel
→ Saves half the time
```

### Use Case 3: Long-Term Projects, Accumulated Preferences

```
Run 1:   System learns you prefer "clean code, type annotations, Chinese comments"
Run 5:   Agents automatically output in your style — saves significant review time
Run 20:  Agents understand your project conventions better than a new team member
```

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/preference-workflow-engine.git
cd preference-workflow-engine

# 2. Configure
cp .env.example .env
# Edit .env — set DASHSCOPE_API_KEY and/or CLAUDE_API_KEY

# 3. Start
make backend   # → http://localhost:8000/docs
make frontend  # → http://localhost:5173

# 4. Use
# Open browser → Enter a scenario → Watch Agents work → View results
```

**Example input:**
> "Design a microservice e-commerce system with user, order, and payment modules, supporting multi-tenancy"

The system automatically: decomposes tasks → matches/creates Agents → recommends Skills (optional) → assigns models → executes Crew → streams real-time logs → persists results

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Vue 3)                       │
│       Chat · Agent Management · Execution History · Files   │
└─────────────────────────────┬───────────────────────────────┘
                              │ SSE / REST
┌─────────────────────────────▼───────────────────────────────┐
│                     FastAPI (crewai_web)                    │
│                                                              │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │ Orchestrator │  │Agent Generator│  │ Skills Recommender │  │
│  └─────────────┘  └──────────────┘  └────────────────────┘  │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │ Model Router │  │ Crew Executor │  │ Preference Evolver │  │
│  └─────────────┘  └──────────────┘  └────────────────────┘  │
│                         │                                     │
│              ┌──────────▼──────────┐                          │
│              │   Touch Layer (WIP)  │                          │
│              │  Auto-dispatch to    │                          │
│              │  external AI services│                          │
│              └─────────────────────┘                          │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│                        LLM Layer                             │
│  ┌─────────────────┐  ┌──────────────────┐                │
│  │  DashScope       │  │  Claude / OpenAI  │                │
│  │  (Qwen models)   │  │  OpenRouter, etc. │                │
│  └─────────────────┘  └──────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

**Two-layer AI call separation:**

| Layer | Responsibility | Model Used |
|-------|---------------|------------|
| **System AI** | Meta-operations (task decomposition, model assignment, preference proposals) | Standard (fixed) |
| **Execution AI** | Actual work (analysis, architecture, documentation, code scaffolding) | Auto-assigned |

---

## Comparison

| Capability | This Project | CrewAI | Dify | AutoGen |
|-----------|-------------|--------|------|---------|
| **Preference Evolution** | ✅ Auto closed-loop | ❌ | ❌ | ❌ |
| **Dynamic model assignment** | ✅ 3-tier auto-routing | ⚠️ Manual | ⚠️ Manual | ❌ |
| **Architecture doc output** | ✅ Core capability | ❌ | ❌ | ❌ |
| **Touch layer** | ✅ Planned | ❌ | ❌ | ❌ |
| **Chinese LLMs (Qwen)** | ✅ Native support | ⚠️ | ✅ | ❌ |
| **SSE real-time logs** | ✅ Full | ❌ | ⚠️ | ❌ |
| **Skills auto-recommendation** | ✅ Optional, non-blocking | ❌ | ❌ | ❌ |
| **Open source** | ✅ MIT | ✅ | ✅ | ✅ |

**Differentiator:** Not an AI coding tool — an AI architecture design copilot.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Agent Orchestration** | [CrewAI](https://crewai.com) |
| **Backend API** | FastAPI + Pydantic v2 + Uvicorn |
| **Frontend** | Vue 3 + TypeScript + Element Plus |
| **LLM Providers** | DashScope (Qwen models, native), Claude (Anthropic) |
| **Persistence** | JSON files (`storage/`) — upgradeable |
| **Python Management** | `uv` |

---

## Project Structure

```
crewai_web/
├── core/
│   ├── ai/            # LLM client + prompt loader
│   ├── llm/           # Provider implementations (DashScope, Claude)
│   ├── chain/         # Chain-of-responsibility execution engine
│   └── tools/         # Skill / Tool loader
├── web/
│   ├── services/      # Business logic (orchestrator, agent generator, preference evolution...)
│   ├── api/           # FastAPI routes
│   ├── domain/        # Pydantic models
│   └── runner/        # Crew execution engine
└── prompts/           # LLM prompt templates

frontend/src/           # Vue 3 SPA
.crew/
├── system_rules.md    # System rules (static, manually maintained)
└── preferences.md     # Personal preferences (dynamic, auto-evolving)
```

---

## Current Status

**MVP completed:**
- [x] Full pipeline: scenario → task decomposition → Agent matching/creation → Skills recommendation → Crew assembly → execution → result persistence
- [x] Auto-injection of preferences into Agent system prompts
- [x] Three-tier model configuration + LLM factory
- [x] SSE real-time execution logs
- [x] Execution history + artifact browsing
- [x] Web UI (Agent / Task / Crew / Skills management)
- [x] Native Chinese LLM support (Qwen via DashScope)
- [x] LLM debug logging (model + trace_id)

---

## Roadmap

The following features are planned, listed by priority.

### Preference Evolution 2.0 — Rule Tagging System

Manage preference rules as **tags**, enabling fine-grained adaptation:

| Feature | Description |
|---------|-------------|
| **Consolidation** | Periodically merge semantically similar rules to keep system prompts lean and save tokens |
| **Confidence scoring** | Rules triggered more frequently gain higher confidence; high-confidence rules are prioritized |
| **Rule provenance** | Each rule tracks its origin (which execution, which scenario), forming an audit trail |
| **Conflict detection** | When rules conflict, resolve by confidence comparison; if confidence is close, ask the user |
| **Competitive queue** | New rules carry confidence scores and compete with existing rules; only winners stay |

### Touch Layer — Auto-Dispatch to External AI Services

Don't limit AI to "writing code." After architecture docs are confirmed, the system can auto-dispatch to:

- **Code generation** → Claude Code / Cursor
- **Industry reports** → Qwen / Kimi
- **Music / Video generation** → Midjourney, Suno, etc.
- **Data processing** → Python / SQL execution services

### More Planned

- **Multi-tenancy** — Independent preference spaces, execution history, and Skills per user/team
- **OpenRouter unified access** — Connect to global mainstream models
- **Enhanced Crew orchestration** — Async parallel, conditional routing, pipeline mode

---

## Positioning

```
AI coding tools (Cursor / Windsurf / Claude Code)
  → Solve "how to write"

AI architecture design tool (this project)
  → Solve "how to design"
  → Decompose complex scenarios into actionable architecture docs
  → Engineers take the docs to their IDE for implementation
```

The developer's value shifts from "writing code" to "architecture design + boundary definition + human review." AI handles decomposition and analysis; humans handle judgment and decisions.

---

## License

MIT License — free for personal and commercial use.

---

## About This Project

This project started from a simple curiosity: **What does "Crew" mean in CrewAI, and how does it work?**

Driven by that question, building while learning, what started as an experiment became a complete AI workflow engine.

It started with one person, driven by curiosity. No funding, no team — just one honest assessment: the value of AI Agents isn't in "writing code for you," but in "helping you decompose complex problems clearly."

Whether that's right — time will tell.

---

> **Design Philosophy**
>
> This project is for developers who want AI Agents that continuously learn, rather than starting from scratch every time. Core insight: **The most valuable AI system isn't the one with the strongest model — it's the one that understands you best.**
