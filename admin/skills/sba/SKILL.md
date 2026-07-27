# SBA Agent — Skill Reference

## Role
**Sales/Business Agent** — TAGS Agency ka lead engine. Leads dhundhta hai, qualify karta hai, meetings karta hai, aur jab lead ready ho toh CEO ko handoff karta hai. Agency-level agent hai, per-workspace nahi.

## Core Principles
- **Full lifecycle ownership** — Lead discovery se lekar Client Handoff tak sab SBA ka kaam hai
- **24/7 always-on** — Pipeline continuously chalta rehta hai, kabhi nahi rukega
- **Multi-language** — Hindi, Hinglish, English — kisi bhi language mein meeting/notes
- **Chrome browser** — Real browser se LinkedIn, Upwork, freelancer platforms par prospecting
- **Multi-phase thinking** — Har decision pe deep analysis (LangGraph)
- **Autonomous** — CEO ka wait nahi karta, khud leads dhundhta hai aur qualify karta hai

## Architecture

```
SBA Agent (Agency-levelGraph StateGraph (multi-phase thinking)
│   ├── call_llm → route → run_tools → finalize
│   └── Chrome browser tool-calling
├── ChromeTool (dedicated real browser)
│   ├── LinkedIn prospecting
│   ├── Freelancer platforms (Upwork, Fiverr)
│   └── Social media research
├── SBA Store (Leads + Meetings + Handoffs)
│   ├── PostgreSQL persistence
│   └── In-memory cache for speed
├── SBA Skills (auto-detected from Jcode catalog)
│   ├── cold-outreach (8 proven sales systems)
│   ├── alex-hormozi-pitch (irresistible offers)
│   ├── sales-enablement (collateral + proposals)
│   ├── lead-qualification (CHAMP/BANT/MEDDIC)
│   └── meeting-companion (scheduling + follow-up)
└── Agent Bus (CEO + Workspace agents se communicate)
```

## 24 API Endpoints

### Status & Chat
| Endpoint | Method | Kya Karta Hai |
|----------|--------|---------------|
| `/api/sba/status` | GET | Pipeline summary + SBA status |
| `/api/sba/chat` | POST | Chat with SBA (auto skill detection) |
| `/api/sba/skills` | GET | List available skills |
| `/api/sba/think` | POST | Analyze a sales situation |
| `/api/sba/translate` | POST | Translate any language |

### Lead Management (CRUD)
| Endpoint | Method | Kya Karta Hai |
|----------|--------|---------------|
| `/api/sba/leads` | GET | List all leads (filter by status) |
| `/api/sba/leads` | POST | Create new lead |
| `/api/sba/leads/{id}` | GET | Get single lead |
| `/api/sba/leads/{id}` | PATCH | Update lead |
| `/api/sba/leads/{id}` | DELETE | Delete lead |
| `/api/sba/leads/qualify` | POST | AI-qualify a lead (score 0-100) |
| `/api/sba/leads/{id}/handoff` | POST | Handoff lead to CEO |

### Pipeline
| Endpoint | Method | Kya Karta Hai |
|----------|--------|---------------|
| `/api/sba/pipeline` | GET | Kanban-style pipeline view |
| `/api/sba/finance` | GET | Revenue forecast + deal tracking |

### Meetings
| Endpoint | Method | Kya Karta Hai |
|----------|--------|---------------|
| `/api/sba/meetings` | GET | List meetings |
| `/api/sba/meetings` | POST | Schedule new meeting |
| `/api/sba/meetings/{id}` | GET | Get meeting details |
| `/api/sba/meetings/{id}` | PATCH | Update meeting |
| `/api/sba/meetings/{id}/notes` | POST | Add note (any language) |
| `/api/sba/meetings/{id}/transcript` | POST | Append/analyze/finalize transcript |
| `/api/sba/meetings/{id}/handoff-to-ceo` | POST | Smart handoff with confidence check |

### Handoffs
| Endpoint | Method | Kya Karta Hai |
|----------|--------|---------------|
| `/api/sba/handoffs` | GET | List all handoffs |
| `/api/sba/handoffs/{id}` | GET | Get handoff details |
| `/api/sba/handoffs/{id}/create-workspace` | POST | Link workspace to handoff |

## Workflow (Interview Q13 — Full Lifecycle)

### Phase 1: Lead Discovery
1. **Chrome browser** se LinkedIn, Upwork, communities par leads dhundho
2. **Social listening** — koi apni problem post kar raha hai? Lead banao
3. **In email, WhatsApp se aane wale leads track karo
4. **Multi-threaded** — sab platforms ek saath (Q16)

### Phase 2: Lead Qualification
1. `leads/qualify` endpoint — SBA AI se qualify karao
2. **Score 0-100** — red flags, green flags, next steps identify karo
3. **Multi-phase thinking** — deconstruct → seek → envision → analyse → plan → execute
4. Lead status update: new → contacted → meeting

### Phase 3: Meeting & Nurture
1. `meetings` create karo — schedule + invite
2. Meeting notes add karo (kisi bhi language mein)
3. Transcript append/analyze karo
4. Lead ka response track karo: "haan" / "nahi" / "maybe"
5. Meeting finalize karo with summary + action items

### Phase 4: Handoff to CEO (Q17)
1. **Confidence check** — SBA 80%+ confident hai toh handoff
2. **Structured brief** — client info, needs, scope, key signals
3. **Full data dump** — saari meetings, notes, transcripts, action items
4. CEO ko handoff karo → CEO workspace banata hai → agents ko brief karta hai

### Phase 5: Workspace Linking
1. CEO ne workspace create kar diya
2. Handoff ko workspace se link karo
3. CEO agents ko brief karta hai (parallel blast Q4)

## SBA Skills (Auto-detected)

| Skill | Use Case |
|-------|----------|
| `cold-outreach` | Cold email, DM, LinkedIn outreach templates |
| `alex-hormozi-pitch` | Irresistible offers, value equation, pricing |
| `sales-enablement` | Pitch decks, objection handling, proposals |
| `lead-qualification` | CHAMP/BANT/MEDDIC frameworks, scoring |
| `meeting-companion` | Meeting scheduling, live notes, follow-up |

## Interview Compliance

| Question | Answer | Implementation |
|----------|--------|----------------|
| Q1 — Service Offerings | Full-stack growth packages | SBA sells complete package |
| Q13 — SBA Role & Scope | Full lifecycle: Lead → Handoff → Workspace | Lead CRUD + Handoff + Workspace creation |
| Q14 — Chrome Browser | Dedicated real browser | ChromeTool with workspace isolation |
| Q15 — Daily Rhythm | 24/7 always-on pipeline | Lead pipeline with 7 statuses |
| Q16 — Multi-threaded | Sab platforms ek saath | Parallel lead discovery |
| Q17 — Handoff Protocol | Structured brief + full dump | Brief + full_dump in handoff |
| Q18 — CEO Autonomy | Distributed autonomy | SBA independently decides, CEO reviews |
| Q21 — Error Recovery | CEO routes fix | Handoff to CEO for resolution |

## Communication
- **Reports to**: Agency CEO (primary)
- **Hands off to**: CEO (when lead converts to client)
- **Uses**: Chrome browser for prospecting
- **Translates**: Any language (Hindi/Hinglish/English)
- **Owns**: Lead discovery, qualification, meetings, handoff
