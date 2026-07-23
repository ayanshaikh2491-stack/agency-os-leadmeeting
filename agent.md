# Agent Architecture — TAGS Agency OS

> Formal specification of agents, execution engine, routing, and their relationships.

---

## 1. Architecture Model

**Pattern:** Single-CEO with LangGraph Execution Engine  
**Banned:** CrewAI, LiteLLM, multi-agent crews  
**Framework:** LangGraph + LangChain (direct OpenAI-compatible API)

### Flow

```
Ayan (founder)
  │  talks to
  ▼
Agency CEO (multi-phase thinking, strategic)
  │
  ├── delegates to Workspace CEO (per-client, internal only)
  │     └── delegates to sub-agents (SBA, SEO, Content, Website, Ads, Social)
  │
  └── calls Execution Engineer (LangGraph node, code implementation)
```

### Key Rules

- **Ayan talks ONLY to CEOs** (Agency CEO or any Workspace CEO) — NEVER to sub-agents
- **Workspace CEOs are internal** — they do NOT talk to clients directly (corrected July 9)
- **CEO briefs each sub-agent directly** — SBA Agent is NOT a gateway/scoping layer
- **All agents are sales agents** — they serve TAGS Agency's marketing/sales operations

---

## 2. Tier 1: Agency-Level

### 2.1 Agency CEO

| Field | Value |
|-------|-------|
| **ID** | `agency_ceo` |
| **Role** | TAGS Agency CEO & Strategic Director |
| **Talks to** | Ayan (founder/owner) |
| **Visibility** | All client workspaces |
| **Reports to** | Ayan |

**Behavior:**
- Multi-phase strategic thinking: `Deconstruct → Seek → Envision → Analyse → Plan → Execute`
- Khud sochta hai (thinks independently for agency's benefit)
- Talks to Ayan as founder-to-CEO — strategic, conversational, independent
- Monitors workspace progress, plans agency growth, makes strategic decisions
- Invokes Workspace CEOs and Execution Engineer

**System prompt:** `admin/agency/ceo.py` — ~200-line directive covering agency identity, service catalog, agent definitions, workflow rules, and multi-phase thinking steps.

**Implementation:** `AgencyCEO` class (`admin/agency/ceo.py`):
- Takes model config (name, api_key, base_url) from settings
- `process_message()` → calls `_think()` with multi-phase loop
- `_think()` constructs messages array with system prompt + history + user message
- Makes direct OpenAI-compatible API call (temperature 0.7)
- Returns response string
- **Not yet wired to LangGraph** — currently a raw API call

### 2.2 Execution Engineer

| Field | Value |
|-------|-------|
| **ID** | `execution` |
| **Role** | Execution Engineer |
| **Talks to** | Agency CEO (via LangGraph) |
| **Tools** | Code writing, file system, testing |
| **Max iterations** | 15 |

**Behavior:**
- Takes CEO's task assignment and implements it
- Writes production-grade code
- Tests before reporting done
- Does NOT delegate — single agent execution

**Definition:** `admin/agency/agency_agents.py` — dict-based metadata (not a CrewAI Agent):
```python
execution_agent = {
    "role": "Execution Engineer",
    "goal": "Take the CEO's task assignment and implement it cleanly...",
    "backstory": "You are a sharp execution engineer...",
    "allow_delegation": False,
    "max_iter": 15,
}
```

**Note:** Currently defined but not yet wired into the CEO's execution flow. This is intended to be a LangGraph node that the CEO triggers when implementation work is needed.

---

## 3. Tier 2: Workspace-Level (Per Client)

Each client workspace has a full copy of ALL agent roles:

| Agent | Role | Purpose |
|-------|------|---------|
| **Workspace CEO** | Client Account Director | Orchestrates workspace, briefs sub-agents |
| **SBA Agent** | Sales & Client Relations | Sales, lead handling, client relationships |
| **SEO Agent** | SEO Research & Strategy | Keyword research, SEO strategies |
| **Content Agent** | Content Writer & Strategist | Blog, social, ad copy |
| **Website Agent** | Web Developer & Designer | Build/modify websites |
| **Ads Agent** | Ads Specialist | Ad campaign management |
| **Social Agent** | Social Media Manager | Social media management |
| **Analytics Agent** | Data & Analytics | Performance reports |
| **Memory Agent** | Workspace Memory | Cross-session context |

### 3.1 Workspace CEO

| Field | Value |
|-------|-------|
| **ID** | `ceo` (within workspace) |
| **Role** | Client Account Director |
| **Talks to** | Agency CEO (internal). NOT the client directly. |
| **Reports to** | Agency CEO |

**Behavior:**
- Receives brief from Agency CEO about a client
- Briefs each sub-agent individually (SBA Agent does NOT act as gateway)
- All sub-agents work in parallel per CEO direction
- CEO reviews all sub-agent outputs together
- Reports results to Agency CEO

### 3.2 Sub-Agent Autonomy Model

- **Fully autonomous + CEO review** (confirmed Q5, July 9):
  1. CEO briefs all sub-agents simultaneously
  2. Each sub-agent works autonomously — makes its own decisions (tech stack, design, copy, approach)
  3. All sub-agents submit output
  4. CEO reviews everything together
  5. CEO delivers/approves

### 3.3 Service Model (Sub-Agent Scope)

Hierarchy from broadest to most specific (confirmed Q7, July 9):

1. **Agent decides (D — primary mode):** Based on CEO brief, agent decides exactly what to deliver using its own expertise
2. **Fixed package (B):** Predefined core services within client's plan boundaries
3. **Core + add-ons (C):** Special offers, premium add-ons, lower-price plan variants

---

## 4. Agent Definitions (Implementation Status)

### 4.1 Defined in Code

| Agent | File | Status |
|-------|------|--------|
| Agency CEO | `admin/agency/ceo.py` | Working — raw OpenAI call |
| Execution Engineer | `admin/agency/agency_agents.py` | Defined, not wired |
| Workspace CEO | `admin/workspace/manager.py` (default system prompt) | Stub |
| SBA Agent | `admin/workspace/manager.py` (default system prompt) | Stub |
| SEO Agent | `admin/workspace/manager.py` (default system prompt) | Stub |
| Content Agent | `admin/workspace/manager.py` (default system prompt) | Stub |
| Website Agent | `admin/workspace/manager.py` (default system prompt) | Stub |
| Analytics Agent | `admin/workspace/manager.py` (default system prompt) | Stub |

### 4.2 Not Yet Defined

| Agent | Notes |
|-------|-------|
| Ads Agent | In ARCHITECTURE.md, no code yet |
| Social Agent | In ARCHITECTURE.md, no code yet |
| Memory Agent | In workspace_manager default types, no real implementation |

---

## 5. Execution Engine (LangGraph)

### Current State

The execution engine is partially implemented:

1. **AgencyCEO** makes direct API calls to the LLM (not through LangGraph yet)
2. **Execution Engineer** is a dict-based definition waiting to be wired as a LangGraph node
3. **Workspace agents** are simple system-prompt + API-call stubs

### Intended LangGraph Flow

```
[User Message]
     │
     ▼
Agency CEO Node (multi-phase thinking)
     │
     ├──► [Decision: needs code?] ──► Execution Engineer Node
     │
     ├──► [Decision: workspace task?] ──► Workspace CEO Node
     │                                    │
     │                                    └──► Sub-agent nodes (parallel)
     │
     └──► [Decision: direct reply] ──► Output
```

### LangGraph Dependencies

Installed via `admin/requirements.txt`:
- `langgraph`
- `langchain-core`
- `langchain-openai`
- `langchain-community`

---

## 6. API Layer

### Routes

| Endpoint | Method | Purpose | Handler |
|----------|--------|---------|---------|
| `/api/chat/ceo` | POST | Chat with Agency CEO | `admin/api/routes/ceo.py` |
| `/api/workspace/create` | POST | Create workspace | `admin/api/routes/workspace.py` |
| `/api/workspace/list` | GET | List workspaces | `admin/api/routes/workspace.py` |
| `/api/workspace/{ws_id}/chat` | POST | Chat with workspace agent | `admin/api/routes/workspace.py` |
| `/api/workspace/{ws_id}` | DELETE | Delete workspace | `admin/api/routes/workspace.py` |
| `/api/health` | GET | Health check | `admin/main.py` |

### Pydantic Schemas

- `ChatRequest(message, conversation_id?, workspace_id?)`
- `ChatResponse(response, conversation_id, workspace_id?)`
- `WorkspaceCreate(name, client_info?)`
- `WorkspaceOut(id, name, client_info?, created_at, agents?)`
- `HealthResponse(ceo_ready, workspace_count)`

---

## 7. Configuration

All via environment variables / `.env` file:

| Variable | Default | Purpose |
|----------|---------|---------|
| `AGENCY_CEO_MODEL` | `llama-3.3-70b-versatile` | CEO model |
| `AGENCY_CEO_API_KEY` | `""` | CEO API key |
| `AGENCY_CEO_API_BASE` | `""` | CEO API base URL |
| `WORKSPACE_AGENT_MODEL` | `llama-3.1-8b-instant` | Workspace agent model |
| `WORKSPACE_API_KEY` | `""` | Workspace API key |
| `WORKSPACE_API_BASE` | `""` | Workspace API base URL |
| `ADMIN_HOST` | `0.0.0.0` | Server host |
| `ADMIN_PORT` | `9002` | Server port |
| `EC2_BACKEND_URL` | `http://18.213.66.136:8000` | EC2 proxy target |
| `DATABASE_URL` | `postgresql+asyncpg://letta:letta@0.0.0.0:5432/tags_agency` | PostgreSQL |
