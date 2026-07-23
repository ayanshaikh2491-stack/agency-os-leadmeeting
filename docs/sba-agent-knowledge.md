# SBA Agent — Knowledge Base

## Definition
**SBA = Sales & Business Agent**
Ek sales agent jo TAGS Agency ki **saari services sell karta hai** + leads find karta hai using its dedicated Chrome browser.

## Core Architecture
- **SBA class**: `admin/agency/sba.py` — `SBAAgent` with multi-phase thinking (6 phases)
- **Chrome tool wrapper**: `admin/tools/chrome_tool.py` — `ChromeTool` class + 12 chrome_* functions
- **Function-calling loop**: SBA calls chrome functions via OpenAI, gets results, continues thinking
- **Dedicated browser**: `chrome-agent/target/release/chrome-agent.exe` (2.4 MB Rust binary)

## Role & Responsibilities (End-to-End)
- **Lead discovery** — Uses Chrome browser to find leads on LinkedIn, Upwork, Fiverr, cold email, Reddit
- **Lead qualification** — Determine fit, budget, authority, need, timeline
- **Nurture relationships** — Build pipeline through follow-ups and engagement
- **Hand off to CEO** — Structured brief + full data dump when lead converts

## Chrome Browser Capabilities
SBA controls a real Chrome browser via function calling:

| Function | Purpose |
|----------|---------|
| `chrome_goto(url)` | Navigate to any URL |
| `chrome_inspect()` | Read page structure, get element UIDs |
| `chrome_click(uid)` | Click buttons, links |
| `chrome_fill(value, uid)` | Type into search boxes |
| `chrome_extract()` | Extract structured data (lead lists) |
| `chrome_text()` / `chrome_read()` | Read page content |
| `chrome_scroll()` | Load more content |
| `chrome_wait()` | Wait for conditions |

**Lead gen workflow:** `goto → inspect → fill/click → extract → read`

## Communication Model
- Talks **only to CEO** (Agency CEO at agency level, Workspace CEO inside workspace)
- CEO gives strategic context; SBA executes autonomously ("khud sochega")
- When lead converts, SBA hands off clean structured brief + full data dump

## Where SBA Runs
| Level | Endpoint | Purpose |
|-------|----------|---------|
| **Agency-level** | `POST /api/chat/sba` | TAGS Agency's OWN lead generation |
| **Workspace-level** | `POST /api/workspace/{ws_id}/chat` (agent_type=sba) | Per-client sales inside workspace |

## Multi-Phase Thinking
1. **Deconstruct** — Break request into atomic components
2. **Seek** — Surface relevant context
3. **Envision** — 2-3 sales approaches, consider using Chrome
4. **Analyse** — Evaluate each approach
5. **Plan** — Choose best approach, call chrome_* functions if browsing needed
6. **Execute** — Final response for CEO

## Behavioural Rules
- Sales expert, not delivery agent
- Direct — weak lead ho to bolo
- Hinglish when it helps
- Action-oriented, concrete next steps
- Clean handoff with structured brief

## Active Files
| File | Purpose |
|------|---------|
| `admin/agency/sba.py` | SBAAgent class with Chrome tool-calling loop |
| `admin/tools/chrome_tool.py` | ChromeTool wrapper + 12 chrome_* tool defs |
| `admin/api/routes/sba.py` | Agency-level SBA endpoint (`POST /api/chat/sba`) |
| `admin/api/routes/workspace.py` | Routes workspace chat to SBA |
| `admin/skills/sba/SKILL.md` | SBA skill definition |
| `admin/config/settings.py` | Chrome-agent path config |
| `chrome-agent/` | Dedicated Chrome browser Rust binary |

## SBA Store & Endpoints (19 Routes)

- **`admin/agency/sba_store.py`** — In-memory store for leads, meetings, handoffs
- **19 FastAPI endpoints** on `/api/sba/`:
  | Endpoint | Purpose |
  |----------|---------|
  | `GET /api/sba/status` | Agent status + pipeline summary |
  | `POST /api/sba/chat` | Chat with SBA (+ Chrome tool-calling) |
  | `GET /api/sba/leads` | List leads (optional `?status=`) |
  | `POST /api/sba/leads` | Create new lead |
  | `GET /api/sba/leads/{id}` | Get lead detail |
  | `PATCH /api/sba/leads/{id}` | Update lead |
  | `DELETE /api/sba/leads/{id}` | Delete lead |
  | `GET /api/sba/pipeline` | Kanban pipeline data (stages) |
  | `GET /api/sba/meetings` | List meetings (`?lead_id=`) |
  | `POST /api/sba/meetings` | Schedule meeting |
  | `GET /api/sba/meetings/{id}` | Meeting details |
  | `PATCH /api/sba/meetings/{id}` | Update meeting |
  | `POST /api/sba/meetings/{id}/notes` | Add note (any language) |
  | `POST /api/sba/leads/{id}/handoff` | **SBA → CEO handoff** |
  | `GET /api/sba/handoffs` | List handoffs |
  | `GET /api/sba/handoffs/{id}` | Get handoff detail |
  | `POST /api/sba/handoffs/{id}/create-workspace` | Link workspace |
  | `GET /api/sba/finance` | Deal overview & forecast |
  | `POST /api/sba/leads/qualify` | Qualify lead via SBA |

## Handoff Flow (SBA → CEO)

```
Lead interested → SBA schedules meeting
→ Meeting happens → SBA takes notes (ANY language: Hi, Hinglish, English)
→ SBA tracks lead_response: "haan" / "nahi" / "maybe"
→ When "haan" → SBA calls POST /api/sba/leads/{id}/handoff
  → Creates structured brief (name, biz, needs, score, next steps)
  + full data dump (all meetings, all notes, all action items)
→ CEO notified with brief + full dump
→ CEO creates workspace for client → workspace_id linked back
```

**Key:** SBA never creates workspace. SBA hands off context. CEO creates workspace.

## Frontend
- Proxy at `agency-frontend/src/app/api/sba/route.js` → `BACKEND_API_URL + /api/sba`

## Build Status
✅ Multi-phase thinking engine
✅ Chrome tool wrapper (12 functions)
✅ Function-calling loop
✅ Agency-level SBA route (`POST /api/chat/sba`)
✅ SBA store with 19 endpoints (leads, meetings, pipeline, handoff, finance, qualify)
✅ Frontend proxy pointing to admin backend
✅ Handoff flow (SBA → CEO structured brief + full dump)
✅ Multi-language meeting notes support
✅ Workspace route integration
✅ Dedicated Chrome binary compiled
✅ Skill file documented

⏳ In Progress / Future:
- 24/7 auto-run scheduler (SBA continuously finds leads)
- PostgreSQL persistence
- Multi-threaded outreach (LinkedIn + Upwork + Fiverr simultaneously)
- LinkedIn-specific workflow template
- Upwork/Fiverr-specific workflow template
- CEO notification system after handoff

