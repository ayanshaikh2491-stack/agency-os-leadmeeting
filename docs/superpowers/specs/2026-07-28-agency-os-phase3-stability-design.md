# Agency OS Phase 3 — Stability, Persistence & Multi-Workspace Hardening

**Date:** 2026-07-28
**Status:** Design Approved

## Objective

Move the Agency from in-memory-only to persistent SQLite storage across all critical components, add CEO proactive monitoring, wire the end-to-end SBA→CEO→Agent flow, and ensure the CEO can see/manage multiple workspaces plus "baki sab" (infra, tokens, alerts).

## Scope

4 implementation phases (not sequential — each self-contained):

1. **SQLite Persistence** — Workspace manager, agent bus, CEO data layer
2. **CEO Proactive Scheduler** — Background heartbeat, alerts, scheduled reports
3. **Agent Retry logic, circuit breaker, better fallbacks
4. **End-to-End Integration Test** — Verify complete pipeline

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    TAGS AGENCY                        │
│                                                       │
│  ┌──────────────────────────────────────────────┐    │
│  │           Agency CEO (ceo.py)                │    │
│  │  • Multi-workspace oversight                 │    │
│  │  • Cross-workspace knowledge                 │    │
│  │  • "Baki sab" — infra, tokens, alerts        │    │
│  │  • Proactive scheduler (new)                 │    │
│  └──────────┬──────────────────────┬────────────┘    │
│             │                      │                   │
│  ┌──────────┴──────────┐  ┌───────┴────────┐          │
│  │  Workspace Manager  │  │  CEO Data      │          │
│  │  (SQLite persistent)│  │  (SQLite)      │          │
│  │  — workspaces       │  │  — activity    │          │
│  │  — reviews          │  │  — knowledge   │          │
│  │  — errors           │  │  — tokens      │          │
│  └──────────┬──────────┘  └────────────────┘          │┐                               │
│  │  Agent Bus          │                               │
│  │  (SQLite persistent)│                               │
│  │  — messages         │                               │
│  │  — knowledge base   │                               │
│  └──────────┬──────────┘                               │
│             │                                          │
│ ──────────┬──────────┬──────────┐         │
│  ▼          ▼          ▼          ▼          ▼         │
│ SEO      Ads      Content    Social   Website/Analytics│
│ (persist  (persist   (persist   (persist   via shared  │
│  to sba   via sba   via sba    via sba    SQLite)      │
│  store)   store)    store)     store)                  │
└─────────────────────────────────────────────────────┘
```

## Step 1: SQLite Persistence

### What changes

| Component | Currently | After |
|-----------|-----------|-------|
| `workspace/manager.py` | In-memory dicts | SQLite tables: `workspaces`, `agent_outputs`, `reviews`, `error_logs` |
| `workspace/agent_bus.py` | `_messages: dict`, `_knowledge: dict` | SQLite tables: `agent_messages`, `agent_knowledge` |
| `ceo_data.py` | Mostly in-memory (some DB reads) | Full SQLite backing for activity log, knowledge, token health |

### Design

- **SQLite** via `aiosqlite` (already a dependency)
- **New file:** `admin/persistence.py` — shared Session/engine for agent-level stores
- **Existing `database.py`** unchanged (still used by SBA's PostgreSQL models)
- **What CEO sees:** `get_agency_overview()` now reads from SQLite → returns ALL workspaces + infra data

### Tables (in `tags_agency_workspace.db`)

```sql
CREATE TABLE workspaces (
  id TEXT PRIMARY KEY,
  name TEXT, client_name TEXT, description TEXT,
  agents TEXT,  -- JSON list
  client_context TEXT,  -- JSON dict
  created_at TEXT
);

CREATE TABLE agent_outputs (
  id TEXT PRIMARY KEY,
  workspace_id TEXT, agent_type TEXT,
  task TEXT, output TEXT, output_preview TEXT,
  timestamp TEXT, reviewed INTEGER DEFAULT 0
);

CREATE TABLE reviews (
  id TEXT PRIMARY KEY,
  workspace_id TEXT, agent_type TEXT,
  output_id TEXT, verdict TEXT, feedback TEXT,
  timestamp TEXT
);

CREATE TABLE error_logs (
  id TEXT PRIMARY KEY,
  workspace_id TEXT, error_type TEXT,
  severity TEXT, description TEXT,
  routed_to TEXT, timestamp TEXT, resolved INTEGER DEFAULT 0
);

CREATE TABLE agent_messages (
  id TEXT PRIMARY KEY,
  from_agent TEXT, to_agent TEXT, workspace_id TEXT,
  message_type TEXT, subject TEXT, content TEXT,
  metadata TEXT, timestamp TEXT,
  read INTEGER DEFAULT 0, responded INTEGER DEFAULT 0
);

CREATE TABLE agent_knowledge (
  id TEXT PRIMARY KEY,
  workspace_id TEXT, domain TEXT,
  learning TEXT, source_workspace TEXT,
  timestamp TEXT
);

CREATE TABLE ceo_activity_log (
  id TEXT PRIMARY KEY,
  workspace_id TEXT, agent_type TEXT,
  action TEXT, details TEXT, metadata TEXT,
  timestamp TEXT
);
```

### Migration

- First run: create tables, copy in-memory data to SQLite
- After: always read/write SQLite
- Graceful fallback: if SQLite fails, return to in-memory

## Step 2: CEO Proactive Scheduler

### New file: `admin/agency/ceo_monitor.py`

A background asyncio task that runs every 15 minutes and:

1. Checks token health → alerts CEO if tokens expiring/expired
2. Checks pending reviews → "X reviews pending, review karo"
3. Checks SBA handoffs → "Y handoffs waiting for CEO"
4. Checks workspace activity → "Z workspace inactive for 7 days"

### CEO Monitor's `get_agency_status()` method

Returns a consolidated `dict` for CEO to use:

```python
{
  "workspaces": [...],           # All workspaces
  "alerts": [...],               # CEO-level alerts
  "leads": {...},                # SBA leads summary
  "tokens": {...},               # Token health
  "pending_reviews": [...],      # Cross-workspace
}
```

### Integration

- `admin Start background task on `startup` event
- Logs status every cycle
- Can be queried via `GET /api/ceo/status` endpoint

## Step 3: Agent Resilience

### Changes to `workspace/manager.py` → `route_to_agent()`

| Current Problem | Fix |
|----------------|-----|
| Agent import fails → fallback LLM | Async retry (3×) before fallback |
| Tool execution fail → crash | Wrap in timeout, catch + route to CEO |
| Content agent miswired | Dynamic agent routing table |

### Retry Decorator

```python
async def route_to_agent(ws_id, agent_type, message):
    for attempt in range(3):
        try:
            response = await agent.chat(message)
            return response
        except TimeoutError:
            log(f"Agent {agent_type} timeout, retry {attempt+1}/3")
        except Exception as e:
            log(f"Agent {agent_type} error, retry {attempt+1}/3: {e}")
            await asyncio.sleep(2 ** attempt)
    return f"{agent_type} failed after 3 retries. CEO should investigate."
```

## Step 4: End-to-End Integration Test

### New file: `admin/tests/test_e2e_ceo_flow.py`

Tests the full pipeline:

1. ✅ CEO import + tools loaded
2. ✅ Workspace create → SQLite persists
3. ✅ Agent bus send/receive
4. ✅ CEO delegate → agent responds
5. ✅ Store agent output → pending review
6. ✅ CEO review → verdict stored
7. ✅ CEO proactive status works
8. ✅ CEO sees multiple workspaces simultaneously

## Files Changed

| File | Action |
|------|--------|
| `admin/persistence.py` | **NEW** — shared SQLite persistence layer |
| `admin/workspace/manager.py` | UPDATE — migrate dicts → SQLite |
| `admin/workspace/agent_bus.py` | UPDATE — migrate dicts → SQLite |
| `admin/ceo_data.py` | UPDATE — read from SQLite, add activity log table |
| `admin/agency/ceo_monitor.py` | **NEW** — proactive background scheduler |
| `admin/main.py` | UPDATE — start monitor on startup |
| `admin/api/routes/ceo.py` | UPDATE — add `/api/ceo/status` endpoint |
| `admin/tests/test_e2e_ceo_flow.py` | **NEW** — end-to-end flow tests |
| `admin/agency/ceo.py` | UPDATE — retry in tool exec, add status query |

## Non-Goals

- PostgreSQL migration (SBA already has it, workspace layer stays SQLite)
- UI/Frontend changes
- Real email sending for alerts (just CEO console for now)
- Per-agent persistence overhaul (each agent already saves its own data via tools)
