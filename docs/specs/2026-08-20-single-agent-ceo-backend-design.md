# Single-Agent Backend (CEO Michael) — Design & Redesign Notes

**Date:** 2026-08-20
**Status:** Implemented & deployed (commit `42e17af`, live on EC2 `18.213.66.136:8000`)

## Context

The original backend (`admin.main`) was a multi-agent orchestration system: an
always-on `agent_loop`, an `agent_monitor`, an organic post scheduler, and a
graph of specialist workers (SBA, SEO, Website, Ads, Content, Social, Analytics).
It was complex, fragile, and crashed on boot because two referenced symbols were
never actually implemented/committed:

1. `append_agent_activity_log` / `get_agent_activity_log` were imported by
   `workers.py` and `ceo.py` but **never defined** anywhere (not committed, not
   in the stash, not on disk). → `ImportError` at module load → every CEO route
   returned 500, including `/api/ceo/state`.
2. `admin/tools/together_gpu.py` was excluded by `.gitignore`, so it never
   reached the GitHub deploy bundle. `content.py` imported it at module top →
   `ModuleNotFoundError` whenever the agent loop ticked content work.

Boss decision: **drop the complex multi-agent system. One agent — CEO Michael —
does everything**: talks to the boss (control room), emails clients, and executes
the work itself (CEO-gated, manual). Frontend (Munder-Difflin office) stays as
built; backend API contract preserved.

## Design

- **CEO Michael is the only live agent.** No auto worker loop, no health monitor,
  no scheduler, no schedule seeding at startup.
- **Startup (`admin/main.py` lifespan):** init persistence + DB, load SBA/workspace
  data from SQLite, seed `ws_agency` / `ws_default` workspaces, register the CEO
  controller + mandate table. Then `yield`. Clean shutdown.
- **Activity tracking:** `append_agent_activity_log` / `get_agent_activity_log`
  now implemented in `admin/workspace/manager.py` (in-memory, bounded to 2000
  lines). Drives the Control Room transcript. `update_agent_activity` already
  existed.
- **GPU module:** `together_gpu.py` un-ignored and committed so the content
  routes import resolves. If it is ever absent, only the image/video generation
  endpoints fail (503), never the whole API.
- **CEO gate preserved:** `POST /api/agents/{slug}/chat` returns **426** for any
  worker slug (workers are CEO-gated; boss must go through CEO). Proven live.

## Endpoints (frontend-safe, unchanged contracts)

- `/api/health` ✓
- `/api/ceo/state`, `/api/ceo/chat`, `/api/ceo/digest`, `/api/ceo/ws/office` ✓
- `/api/agents/{slug}/chat` → 426 (CEO gate) ✓
- `/api/communication/*` (email send, used by CEO) ✓
- Legacy `/api/status`, `/api/chat/agency` ✓

## Verification

- Local: `python -c "import admin.main"` → `IMPORT_OK`
- Live EC2: `/api/health` ok (3 workspaces), `/api/ceo/state` returns CEO shape
  (no 500), `/api/agents/sba/chat` → 426.

## Out of scope (future)

- Re-enabling specialist agents as CEO tools (only if boss wants parallelism).
- Real LLM wiring for CEO chat (uses existing `AgencyCEO`).
- Frontend is built separately and deployed on Vercel; not changed here.
