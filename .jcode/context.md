# TAGS Agency OS — Full Context for Jcode

## Project
- **Name**: TAGS Agency OS
- **Path**: `C:\Users\TAUSHEF\Downloads\int`
- **Owner**: Ayan Shaikh (ayanshaikh2491@gmail.com)
- **Stack**: FastAPI Python backend (port 9002) + Next.js frontend
- **LLM**: Groq Llama (CEO: llama-3.3-70b, agents: llama-3.1-8b)
- **Omnirouter**: `jcode` CLI ka default LLM provider (openai-compatible).
  - Asli config file: `~/.jcode/config.toml` (jcode yahi padhta hai). `~/.jcode/config.json` omniroute dashboard ka managed copy hai (redundant, harmless).
  - `config.toml`: `default_provider = "omnirouter"`, `default_model = "auto/best-coding"` (→ gpt-5.5, strong agentic coder).
  - Omnirouter chalti hai **localhost:20128** (internal 20131) — user ne "2128" bola tha but actual **20128** hai.
  - Omnirouter `auth = "none"` (api key nahi chahiye, bina key bhi accept karta hai). API key file: `~/.config/jcode/provider-9router.env`.
  - Tool-calling verified working (coding models support tools) → jcode real kaam karta hai, sirf chat nahi.
  - **jcode restart zaroori** jab bhi config badle (config startup pe read hota hai).
- **DB**: PostgreSQL configured (asyncpg) but inactive — in-memory only currently
- **Lang**: LangGraph + LangChain (CrewAI permanently banned, LiteLLM permanently banned)

## Architecture (2-Tier LangGraph)

Ayan (owner)
  └── Agency CEO (strategic, multi-phase thinking)
        ├── Workspace CEO (per client, internal only — NEVER talks to clients)
        │     ├── SBA Agent (Sales & Business — leads, outreach, closing)
        │     ├── SEO Agent
        │     ├── Content Agent (visual-only, uses Kaggle API for GPU)
        │     ├── Website Agent
        │     ├── Ads Agent (Meta + Google primary)
        │     ├── Social Agent (strategist, not executor)
        │     └── Analytics Agent
        └── Execution Engineer (code)

## Critical Rules
1. CrewAI/LiteLLM permanently banned — LangGraph only
2. Workspace CEOs internal only — NEVER talk to clients directly
3. CEO hamesha sab agents ko brief karega (parallel blast), SBA agent nahi
4. SBA owns lead stage entirely. CEO activates only post-conversion
5. SBA = sales/pre-sales NOT scoping layer
6. Cross-workspace knowledge sharing: har agent report karega dono ko (Workspace CEO + Agency-level same-role agent)

## Build Status
| Component | Status |
|-----------|--------|
| FastAPI backend (admin/) | ✅ Built — 18+ files |
| Agency CEO (co-founder persona + 9 tools) | ✅ Working — parallel blast, handoff, review, error routing, reports, knowledge sharing |
| SBA Agent (admin/agency/sba.py) | ✅ Multi-phase + Chrome tool-calling loop |
| SBA Store (admin/agency/sba_store.py) | ✅ In-memory leads/meetings/handoff store |
| SBA Routes (23 endpoints) | ✅ Pipeline, meetings, handoff, finance, qualify, translate, think, transcript |
| ChromeTool wrapper (admin/tools/chrome_tool.py) | ✅ 12 chrome_* functions |
| chrome-agent Rust binary | ✅ Compiled (SBA's dedicated browser) |
| SBA skill (admin/skills/sba/SKILL.md) | ✅ Updated with Chrome tool docs |
| SBA knowledge base (docs/sba-agent-knowledge.md) | ✅ Updated (current state) |
| SBA Frontend proxy | ✅ Points to admin backend (port 9002) |
| Workspace Manager | ✅ Built (in-memory) |
| **LangGraph execution engine** | ✅ CEO + 5 workspace agents use LangGraph StateGraphs |
| **Workspace agents (SEO, Content, etc.)** | ✅ Built — 5 domain-specific LangGraph agents (SEO, Ads, Website, Social, Content) |
| **Database persistence** | ❌ In-memory only |
| **Per-agent skill folders** | ✅ Built — SEO, Ads, Website, Social, Content skill docs |

## Build Priority (From Interview Q11)
1. **SBA agent FIRST** — build complete SBA
2. Baaki agents (SEO, Website, Ads, Content, Social)
3. Per-agent skill folders create karna
4. Build ALL services
5. Then think about clients

## CEO Agent Details
- **Location**: `admin/agency/ceo.py` — AgencyCEO class
- **Routes**: `admin/api/routes/ceo.py` — 10 endpoints
- **Co-founder persona (Q19)**: Strategic partner, candid, direct, disagrees respectfully
- **9 Tools**:
  1. `delegate_to_workspace` — single agent delegation
  2. `delegate_parallel_blast` — brief ALL agents simultaneously (Q4)
  3. `list_workspaces` — see all workspaces
  4. `get_workspace_report` — detailed workspace report
  5. `receive_sba_handoff` — process SBA handoff (Q17)
  6. `review_agent_output` — approve/reject agent work (Q20)
  7. `route_error_fix` — error recovery routing (Q21)
  8. `generate_report` — weekly/monthly reports (Q23)
  9. `get_cross_workspace_knowledge` — knowledge sharing (CRITICAL)
- **API Endpoints**:
  - `POST /api/ceo/chat` — Chat with CEO
  - `POST /api/ceo/handoff/receive` — Receive SBA handoff
  - `POST /api/ceo/parallel-blast` — Parallel blast delegation
  - `POST /api/ceo/review` — Review agent output
  - `POST /api/ceo/error/route` — Route error fixes
  - `POST /api/ceo/report` — Generate reports
  - `GET  /api/ceo/knowledge` — Get cross-workspace knowledge
  - `POST /api/ceo/knowledge` — Add learning
  - `GET  /api/ceo/reviews` — List reviews
  - `GET  /api/ceo/errors` — List error logs
  - `POST /api/chat/agency` — Legacy endpoint (backward compatible)

## SBA (Sales & Business Agent) Details
- **Location**:
  - `admin/agency/sba.py` — Agent class (multi-phase thinking + tool-calling)
  - `admin/agency/sba_store.py` — In-memory data store (leads, meetings, handoffs)
  - `admin/api/routes/sba.py` — 23 FastAPI endpoints
  - `admin/tools/chrome_tool.py` — Chrome CLI wrapper (12 functions)
  - `admin/skills/sba/SKILL.md` + `docs/sba-agent-knowledge.md` — Docs
- **Role**: End-to-end lead lifecycle — find leads, qualify, nurture, handoff to CEO
- **Chrome integration**: SBA calls chrome_* functions (goto, inspect, click, fill, extract) via OpenAI function-calling loop (max 10 rounds)
- **Endpoints (23 total):
  - `GET /api/sba/status` — Status + pipeline summary
  - `POST /api/sba/chat` — Chat with SBA (+ Chrome tool-calling)
  - `GET/POST /api/sba/leads` — List/create leads
  - `GET/PATCH/DELETE /api/sba/leads/{id}` — Individual lead CRUD
  - `GET /api/sba/pipeline` — Kanban pipeline data
  - `GET /api/sba/meetings` — List meetings
  - `POST /api/sba/meetings` — Create meeting
  - `GET/PATCH /api/sba/meetings/{id}` — Meeting details
  - `POST /api/sba/meetings/{id}/notes` — Add note (any language!)
  - `POST /api/sba/meetings/{id}/transcript` — Append/analyze/finalize meeting transcript
  - `POST /api/sba/meetings/{id}/handoff-to-ceo` — SBA → CEO handoff from meeting
  - `POST /api/sba/leads/{id}/handoff` — SBA → CEO handoff
  - `GET /api/sba/handoffs` — List all handoffs
  - `GET /api/sba/handoffs/{id}` — Get handoff with full dump
  - `POST /api/sba/handoffs/{id}/create-workspace` — Link workspace
  - `GET /api/sba/finance` — Finance / deal overview
  - `POST /api/sba/leads/qualify` — Qualify lead via SBA thinking
  - `POST /api/sba/translate` — Translate Hinglish ↔ English
  - `POST /api/sba/think` — SBA analyzes a sales situation
- **Frontend proxy**: `agency-frontend/src/app/api/sba/route.js` → `BACKEND_API_URL + /api/sba`
- **Handoff flow**: SBA meeting → notes (any language) → lead says "haan" → SBA calls `POST /api/sba/leads/{id}/handoff` → structured brief + full data dump → CEO gets notified → CEO creates workspace → workspace_id linked back to handoff

## Key Docs
- `ARCHITECTURE.md` — Updated architecture plan (LangGraph migration)
- `agent.md` — Agent architecture formalization
- `handoff.md` — July 9 session handoff
- `letta.md` — Letta Code memory reference
- `docs/sba-agent-knowledge.md` — SBA knowledge base
- `admin/agency/ceo.py` — Agency CEO class
- `admin/agency/sba.py` — SBA agent class

## Interview Summary (July 9-10, 2026)
Full interview file at: `.jcode/interview.md`
- 23 deep questions + sub-agent interviews for ALL agents
- Format: Grill-style multiple-choice (A/B/C/D) — NEVER open-ended
- "Deep se deep" questions, Hinglish preferred
- **Build first, sell later** — confirmed priority

## User Preferences
- Hindi/English mix (Hinglish) — "bhai", "yaar", "dkeho", "kaha hai"
- Wants complete context preservation — doesn't want to re-explain
- Impatient — wants to get to actual work
- Grill-style questions with options, never open-ended

## Memory Log
- **2026-07-13**: `jcode` omnirouter setup check kiya. Asli config `~/.jcode/config.toml` hai (pehle se omnirouter default tha, `coding-fast` model). Verified: omnirouter localhost:20128 pe chal raha, bina API key accept karta hai, tool-calling works. Default model ko `auto/best-coding` (gpt-5.5) set kiya taaki reliable agentic kaam kare — sirf chat na kare. Restart karne pe lagu hoga.
