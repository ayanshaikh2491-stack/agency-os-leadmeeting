# Letta Code — Agent Memory & Context

> This file is memory for the Letta Code agent working on the TAGS Agency OS project.
> It helps future invocations recover context quickly and avoid re-learning.

---

## Project Identity

- **Project:** TAGS Agency OS — AI-powered multi-agent marketing platform
- **Project root:** `C:\Users\TAUSHEF\Downloads\int`
- **Repo type:** Monolith with Next.js frontend (`agency-frontend/`) + Python backend (`admin/`)
- **Owner/founder:** Ayan (Tugal Ayan Shaikh)
- **Communication:** Prefers Hinglish, direct tone, gets frustrated when context is repeated

---

## Architecture at a Glance

```
Ayan (founder)
  │
  ▼
Agency CEO (strategic, multi-phase thinking)
  │
  ├── Workspace CEO (per client — internal only, does NOT talk to clients directly)
  │     └── Sub-agents: SBA, SEO, Content, Website, Ads, Social
  │
  └── Execution Engineer (LangGraph single‑agent execution)
```

### Corrected Design Constraints (confirmed July 9, 2026)

1. **CrewAI is PERMANENTLY BANNED.** Never import, install, or propose it.
2. **LiteLLM is PERMANENTLY BANNED.** Use LangChain + direct OpenAI-compatible calls.
3. **Single CEO architecture.** One Agency CEO + one Execution Engineer. No multi-agent crews.
4. **Workspace CEOs are internal only.** They do NOT talk to clients directly. Only Agency CEO talks to Ayan.
5. **SBA agent = sales/pre-sales only.** SBA is NOT a scoping/gateway layer above other agents. CEO briefs each sub-agent directly.
6. **"SBA" (without "agent")** in conversation means "sab kuch" (everything about the client's business) — NOT the SBA Agent.
7. **All agents are sales agents.** They serve TAGS Agency's marketing/sales clients.
8. **Per-workspace mirrors agency-level structure.** Each workspace has its own CEO + sub-agents.
9. **LangGraph state graphs** for execution flow. Not CrewAI, not plain LangChain.

---

## Codebase Structure (admin/ backend)

```
admin/
├── main.py                      # FastAPI entry point
├── __init__.py
├── config/
│   ├── __init__.py
│   └── settings.py              # Env-based config (models, ports, DB URL)
├── api/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py           # Pydantic models (ChatRequest, WorkspaceCreate, etc.)
│   └── routes/
│       ├── __init__.py
│       ├── ceo.py               # POST /api/chat/ceo
│       └── workspace.py         # CRUD + chat /api/workspace/...
├── agency/
│   ├── __init__.py              # Exports AgencyCEO, execution_agent, execution_task
│   ├── ceo.py                   # AgencyCEO class — multi-phase thinking loop
│   └── agency_agents.py         # Execution Engineer definition + agent/task registry
├── workspace/
│   ├── __init__.py
│   └── manager.py               # In-memory Workspace Manager (CRUD + per-agent chat)
└── tools/
    └── __init__.py
```

### Key Implementation Details

**CEO chat (`admin/api/routes/ceo.py`):**
- `POST /api/chat/ceo` accepts `ChatRequest(message, conversation_id, workspace_id?)`
- Instantiates `AgencyCEO`, calls `process_message()`
- Returns `ChatResponse(response, conversation_id, workspace_id?)`

**Workspace routes (`admin/api/routes/workspace.py`):**
- `POST /api/workspace/create` — Create workspace with client info
- `GET /api/workspace/list` — List all workspaces
- `POST /api/workspace/{ws_id}/chat` — Send message to a specific workspace agent
- `DELETE /api/workspace/{ws_id}` — Delete workspace

**AgencyCEO (`admin/agency/ceo.py`):**
- Multi-phase thinking: `deconstruct → seek → envision → analyse → plan → execute`
- System prompt is a long directive with agency context
- Uses direct OpenAI-compatible API call (no CrewAI, no LangChain wrappers yet)
- Temperature 0.7

**Execution Engineer (`admin/agency/agency_agents.py`):**
- Dict-based agent definition (no CrewAI Agent class)
- Single `execution_agent` with role "Execution Engineer"
- `execution_task_template` expects task_description formatting
- `_AGENT_MAP = {"execution": execution_agent}`

**Workspace Manager (`admin/workspace/manager.py`):**
- In-memory dict of workspaces
- Each workspace: `id`, `name`, `client_info`, agents dict
- Default agents per workspace: `sba`, `seo`, `content`, `website`, `analytics`, `memory`
- Per-agent chat creates a simple LLM call with agent-specific system prompt

**Settings (`admin/config/settings.py`):**
- Free-tier defaults: Groq Llama models
- Agency CEO: `llama-3.3-70b-versatile` by default
- Workspace agents: `llama-3.1-8b-instant` by default
- Port 9002 for admin backend
- PostgreSQL connection string (asyncpg) — not yet used (in-memory only currently)

---

## Frontend (agency-frontend/)

- Next.js app at `C:\Users\TAUSHEF\Downloads\int\agency-frontend`
- Admin pages: `/admin/agents/*`, `/admin/ceo`, `/admin/dashboard`
- Components: `CEOAgentMonitor`, `CEODashboardKPIs`, `CEODecisionLog`, `CEOClientList`
- 9 agent proxy routes under `src/app/api/agents/`
- CEO chat proxies through Hermes at `localhost:9000` (to be replaced)

---

## What Has Been Built vs Planned

### Built
- [x] FastAPI backend scaffold (`admin/main.py`)
- [x] CEO route + chat endpoint (`/api/chat/ceo`)
- [x] Workspace CRUD + chat routes (`/api/workspace/*`)
- [x] Pydantic schemas (`ChatRequest`, `ChatResponse`, `WorkspaceCreate`, `WorkspaceOut`)
- [x] AgencyCEO class with multi-phase thinking (`admin/agency/ceo.py`)
- [x] Execution Engineer agent definition (`admin/agency/agency_agents.py`)
- [x] In-memory Workspace Manager (`admin/workspace/manager.py`)
- [x] Config/settings with env-based overrides
- [x] CORS middleware for frontend integration
- [x] Health endpoint (`/api/health`)
- [x] LangGraph/LangChain deps in requirements
- [x] **ChromeTool wrapper** (`admin/tools/chrome_tool.py`) — 12 chrome_* functions for SBA
- [x] **SBA Chrome integration** — SBA chat uses OpenAI function-calling loop to control chrome-agent

### Not Yet Built / Stub
- [ ] Real LangGraph graph integration (CEO currently uses raw OpenAI API)
- [ ] Execution Engineer actually wired into CEO flow
- [ ] Database persistence (currently in-memory only)
- [ ] Authentic workspace sub-agents (current agents are stubs with system prompts)
- [ ] Per-agent API keys (all agents share workspace key)
- [ ] No CrewAI crew classes (correctly absent — not needed)
- [ ] No `admin/` CrewAI routes proposed in old ARCHITECTURE.md
- [ ] Frontend not yet connected to admin backend for CEO/workspace chat

---

## Documents Created

| File | Purpose |
|------|---------|
| `letta.md` | (this file) Memory for Letta Code agent |
| `agent.md` | Agent architecture & definitions |
| `handoff.md` | Session handoff for next session |
| `ARCHITECTURE.md` | Updated architecture plan |

---

## Known Issues & Gotchas

1. **PowerShell environment**: `&&` chaining doesn't work. Use `;` or separate commands.
2. **SSH quoting**: Complex nested quotes break in PowerShell. Use SCP + execute workaround.
3. **No active services**: LiteLLM (port 4000), EC2 backend, Hermes (port 9000) — none confirmed running.
4. **ARCHITECTURE.md still has CrewAI references** — conceptual parts are correct for two-tier hierarchy, but implementation sections are stale.
5. **No .env at project root** — some settings may not load correctly.
6. **Workspace agents are stubs** — they share the same LLM config and have no real tools/autonomy.
