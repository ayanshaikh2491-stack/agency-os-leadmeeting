# TAGS Agency OS — Architecture Plan

> **⚠️ IMPORTANT — IMPLEMENTATION CORRECTION (July 9, 2026)**
> This document was originally written for a CrewAI-based architecture.
> CrewAI and LiteLLM are **permanently banned**. The actual implementation uses
> **LangGraph + LangChain** with a single CEO + execution engineer pattern.
> Conceptual (two-tier hierarchy, CEO roles, workspace isolation) remains correct.
> All remaining CrewAI references are being migrated to LangGraph.

## 1. Core Architecture: Two-Tier Structure

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    TAGS AGENCY (Owned by Ayan)                          │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    AGENCY CEO (Strategic)                         │   │
│  │  - Talks to Ayan (founder/owner) — strategic, khud sochta hai    │   │
│  │  - Oversees ALL client workspaces                                │   │
│  │  - Gets reports from each workspace's CEO                        │   │
│  │  - Can see what's happening in any client workspace               │   │
│  └────────────┬──────────────┬──────────────────────┬──────────────┘   │
│               │              │                      │                   │
│  ┌────────────┴──────────┐ ┌─┴──────────────┐  ┌────┴──────────────┐   │
│  │ Agency-Level Agents   │ │ Client A        │  │ Client B          │   │
│  │ (for TAGS internal    │ │ Workspace       │  │ Workspace         │   │
│  │  operations)          │ │                 │  │                   │   │
│  │ - Done by Ayan only   │ │ ┌───────────┐   │  │ ┌───────────┐     │   │
│  └───────────────────────┘ │ │Client CEO  │   │  │ │Client CEO │     │   │
│                            │ │- Talks to  │   │  │ │- Talks to │     │   │
│                            │ │ client     │   │  │ │ client    │     │   │
│                            │ │- Reports   │   │  │ │- Reports  │     │   │
│                            │ │ to Agency  │   │  │ │ to Agency │     │   │
│                            │ │ CEO        │   │  │ │ CEO       │     │   │
│                            │ ├───────────┤   │  │ ├───────────┤     │   │
│                            │ │ SBA Agent  │   │  │ │ SBA Agent  │     │   │
│                            │ │ SEO Agent  │   │  │ │ SEO Agent  │     │   │
│                            │ │ Website Ag │   │  │ │ Website Ag │     │   │
│                            │ │ ...        │   │  │ │ ...        │     │   │
│                            │ └───────────┘   │  │ └───────────┘     │   │
│                            └─────────────────┘  └───────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Key Concepts

| Layer | CEO | Talks To | Visibility |
|-------|-----|----------|------------|
| **Agency** | Agency CEO | Ayan (owner) | All client workspaces + agency ops |
| **Client Workspace** | Workspace CEO | Client (directly) | Only that client's workspace |

### 1.1 Agency Layer (TAGS Internal)

- **Agency CEO**: Strategic leader. Talks to Ayan as founder-to-CEO. Khud sochta hai, plans for agency growth, delegates to workspace CEOs. Can see every client workspace, ask questions, pull reports.
- **Agency Agents**: Internal TAGS agents (SBA, SEO, Content, Website) for TAGS's own operations — but main kaam client workspace agents karte hain.
- **Owned by**: Ayan only.

### 1.2 Client Workspace Layer (Per Client)

Har client ka **apna isolated workspace** hota hai:

```
Client Workspace
│
├── Workspace CEO
│   ├── Internal only — does NOT talk to clients directly
│   ├── Receives brief from Agency CEO → briefs sub-agents
│   ├── Sub-agents work autonomously → submit output to CEO
│   ├── CEO reviews all outputs together
│   └── Reports progress → Agency CEO ko bhejta hai
│
├── SBA Agent (client's automation)
├── SEO Agent (client's SEO)
├── Content Agent (client's content)
├── Website Agent (client's web)
├── Ads Agent (client's ads)
├── Social Agent (client's social)
└── Analytics Agent (client's reports)
```

**Important rules:**
- Workspace agents **sirf client ka kaam karte hain** — they don't see other clients
- Workspace CEO **internal only** — does NOT talk to clients (corrected July 9, 2026)
- Only Ayan and Agency CEO talk to clients
- Workspace CEO **Agency CEO ko report bhejta hai** — progress, issues, results
- Agency CEO **sab kuch dekh sakta hai** — har workspace ke status, questions, reports

### 1.3 Reporting Flow

```
Ayan: "Client X ke liye kya ho raha hai?"
  ↓
Agency CEO: Briefs Workspace CEO about Client X's SBA (sab kuch)
  ↓
Workspace CEO Brief → SEO, Content, Website, Ads, Social agents
  │   (parallel blast — all agents work autonomously)
  ├── SEO Agent: Research keywords, audit current site
  ├── Content Agent: Write blog post, social content
  ├── Website Agent: Build/optimize pages
  ├── Ads Agent: Campaign strategy
  ├── Social Agent: Social media plan
  └── Analytics Agent: Performance baseline
  ↓
All agents return output → Workspace CEO reviews together
  ↓
Workspace CEO → Agency CEO: "Client X ke liye sab ready hai — SEO audit, content, ads plan"
  ↓
Agency CEO → Ayan: "Client X pe progress hai — sab agents ne kaam khatam kiya, ab approval needed"
```

### 1.4 Chat Interfaces

```
Ayan → /admin/chat/ceo        (Chat with Agency CEO — strategic oversight)
Ayan → /admin/dashboard       (Agency-level — all workspaces, agents, status)
Ayan → /admin/workspace/{id}  (View workspace detail — skills, tasks, agents)
```

**Clients never interact with the platform directly.** Ayan/CEO handles all client communication. Sub-agents are internal only. (Confirmed July 9, 2026)

---

## 2. Agent Definitions (Two-Tier)

### 2.1 Tier 1: Agency-Level Agents

| Agent | Role | Talks To | Purpose |
|-------|------|----------|---------|
| **Agency CEO** | `TAGS Agency CEO & Strategic Director` | Ayan (owner) | Agency strategy, oversee workspaces, get reports, plan growth |

#### Agency CEO
- **Role**: `TAGS Agency CEO & Strategic Director`
- **Goal**: Run the entire agency. Understand Ayan's vision, oversee all client workspaces, track agency KPIs, and make strategic decisions. Khud sochta hai, plans ahead, behaves like a real CEO talking to the founder.
- **Backstory**: You are the CEO of TAGS Agency. You oversee multiple client workspaces, each with their own CEO and agents. Your job is to talk to Ayan (the founder/owner), understand agency-level goals, check in on workspace progress, and make strategic decisions. You NEVER do client-level work directly — you delegate to workspace CEOs.
- **Tools**: `DelegateWorkTool` (towards workspace CEOs), custom `ListWorkspacesTool`, `GetWorkspaceReportTool`
- **Visibility**: ALL client workspaces

### 2.2 Tier 2: Workspace-Level Agents

Har workspace (har client ke liye) ke apne agents hote hain:

| Agent | Role | Talks To | Reports To |
|-------|------|----------|------------|
| **Workspace CEO** | `Client Account Director & SBA` | Client directly | Agency CEO |
| **SBA Agent** | Small Business Automation Specialist | Workspace CEO | Workspace CEO |
| **SEO Agent** | SEO Research & Strategy | Workspace CEO | Workspace CEO |
| **Content Agent** | Content Writer & Strategist | Workspace CEO | Workspace CEO |
| **Website Agent** | Web Developer & Designer | Workspace CEO | Workspace CEO |
| **Analytics Agent** | Data & Analytics | Workspace CEO | Workspace CEO |

#### Workspace CEO
- **Role**: `Client Account Director & SBA`
- **Goal**: Client ki taraf se kaam karna. Client se seedha baat karna, unke needs samajhna, unke workspace agents ko tasks dena, aur results report karna Agency CEO ko.
- **Backstory**: You are the CEO of this client's workspace at TAGS Agency. Your client sees you as their dedicated consultant/SBA. You talk to them directly, understand their business, delegate to your team (SEO, Content, Website agents), and make sure their goals are met. You also report progress back to the Agency CEO.
- **Tools**: `DelegateWorkTool` (towards workspace agents), custom `GetWorkspaceStatusTool`
- **Behavior**: Client se aise baat karega jaise uska apna business consultant — friendly, practical, proactive
- **Process**: LangGraph state graph (CEO orchestration via structured thinking phases → sub-agent invocation)

#### Workspace SEO Agent
- **Role**: `SEO Research & Strategy Specialist`
- **Goal**: Research keywords, analyze competitors, create SEO strategies for THIS client.
- **Tools**: Web search, keyword research, competitor analysis, rank tracking
- **Scope**: Sirf is client ka kaam

#### Workspace Content Agent
- **Role**: `Content Writer & Strategist`
- **Goal**: Write blog posts, social media content, ad copy for THIS client.
- **Tools**: Writing tools, content briefs from SEO agent
- **Scope**: Sirf is client ka kaam

#### Workspace Website Agent
- **Role**: `Web Developer & Designer`
- **Goal**: Build, modify, maintain THIS client's websites.
- **Tools**: File system access, code generation, deployment
- **Scope**: Sirf is client ka kaam

#### Workspace Analytics Agent
- **Role**: `Data & Analytics Specialist`
- **Goal**: Track THIS client's performance, generate reports.
- **Tools**: Data querying, reporting, visualization
- **Scope**: Sirf is client ka kaam

### 2.3 Key Difference

| Aspect | Agency CEO | Workspace CEO |
|--------|-----------|---------------|
| **Talks to** | Ayan (owner/founder) | Client directly |
| **Sees** | All workspaces | Only their workspace |
| **Reports to** | Ayan | Agency CEO |
| **Focus** | Strategy, growth, oversight | Client delivery, execution |
| **Personality** | Strategic CEO → founder | Consultant → client

---

## 3. Chat-Based Interaction Model

### 3.1 Entry Points (Frontend Routes)

#### Agency Level (Ayan access)
```
/admin/chat/ceo           → Chat with AGENCY CEO (strategic, oversight)
/admin/chat/workspace/{id}→ Chat with a specific workspace's CEO
/admin/dashboard          → Agency-level dashboard — all workspaces
```

#### Workspace Level (Client access — future)
```
/{workspace}/chat         → Chat with that workspace's CEO
/{workspace}/dashboard    → Client's own dashboard
```

### 3.2 Chat Flows

#### Flow 1: Ayan → Agency CEO (Strategic)
```
Ayan: "Agency ka performance kaisa chal raha hai overall?"
  ↓
Agency CEO: Checks all workspace reports
  ↓
Agency CEO: "Client A pe SEO rank improve hua hai, Client B ka naya website launch ready."
```

#### Flow 2: Ayan → Workspace CEO (Deep dive into a client)
```
Ayan: "Client A ke workspace mein kya chal raha hai?"
  ↓
Agency CEO (or direct): Opens Client A workspace
  ↓
Workspace CEO: "Client A ke liye SEO audit complete, ab implementation phase hai..."
```

#### Flow 3: Client → Workspace CEO (Client interaction)
```
Client: "Meri website pe traffic kaise badhau?"
  ↓
Workspace CEO: Analyzes, plans, delegates
  ├── → SEO Agent: "Research keywords for [client domain]"
  ├── → Content Agent: "Write blog post outline for target keywords"
  ├── → Analytics Agent: "Pull current traffic data"
  ↓
Agents return results to Workspace CEO
  ↓
Workspace CEO: "Client, yeh raha detailed plan — [results + next steps]"
  ↓
Workspace CEO → Agency CEO: [Weekly Update] "Client A — SEO plan in motion"
```

#### Flow 4: Workspace CEO → Agency CEO (Reporting)
```
Workspace CEO (auto/scheduled):
  "Client A progress report:
   - SEO audit: ✅ Complete
   - Keyword research: ✅ Complete
   - Blog post 1: 📝 In progress
   - Next: Content publishing next week"
```

### 3.3 Direct Chat (Ayan Bypass)

```
Ayan: "/workspace/client-a status batao"
  ↓
Routes directly to Workspace CEO of Client A
  ↓
Returns current status of all tasks
```

---

## 4. Technical Architecture

### 4.1 Two-Tier Backend Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                   FRONTEND (Next.js)                              │
│  /admin/chat/ceo    /admin/dashboard    /admin/workspace/{id}    │
│  CEOAgentMonitor    ChatWindow          CEODecisionLog            │
└─────────────────────────┬────────────────────────────────────────┘
                          │  REST / WebSocket API (port 9002)
┌─────────────────────────┴────────────────────────────────────────┐
│                   BACKEND — ADMIN SERVICE                          │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐    │
│  │                API ROUTER (FastAPI)                         │    │
│  │  POST /api/chat/agency     → Agency CEO                    │    │
│  │  POST /api/chat/workspace  → Workspace CEO via manager     │    │
│  │  GET  /api/workspaces      → List all workspaces + status  │    │
│  │  GET  /api/workspace/{id}  → Single workspace detail       │    │
│  └───────────────────────┬───────────────────────────────────┘    │
│                          │                                         │
│  ┌───────────────────────┴───────────────────────────────────┐    │
│  │              LANGGRAPH STATE GRAPH (Agency Level)           │    │
│  │                                                             │    │
│  │  Agency CEO Node                                           │    │
│  │  ├── Multi-phase thinking: Deconstruct→Seek→Envision→     │    │
│  │  │   Analyse→Plan→Execute                                  │    │
│  │  └── Calls/invokes sub-agents via tool calls               │    │
│  │                                                             │    │
│  │  Execution Engineer Node                                   │    │
│  │  ├── Receives CEO's plan → executes tasks                  │    │
│  │  └── Reports results back to CEO                           │    │
│  └───────────────────────┬───────────────────────────────────┘    │
│                          │                                         │
│  ┌───────────────────────┴───────────────────────────────────┐    │
│  │     WORKSPACE MANAGER (per-client workspace state)          │    │
│  │                                                             │    │
│  │  Workspace A                                               │    │
│  │  ├── WS_A CEO (LangGraph state graph)                      │    │
│  │  │   ├── Multi-phase thinking node                         │    │
│  │  │   └── Sub-agent executor nodes                          │    │
│  │  ├── WS_A SEO Agent (LLM call node)                        │    │
│  │  ├── WS_A Content Agent (LLM call node)                    │    │
│  │  ├── WS_A Website Agent (LLM call node)                    │    │
│  │  └── WS_A Analytics Agent (LLM call node)                  │    │
│  │                                                             │    │
│  │  Workspace B — same structure                               │    │
│  └─────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

**Key Principle:** Har workspace ka apna isolated LangGraph state graph hota hai. CEO node multi-phase thinking karta hai, then calls/invokes sub-agent execution nodes. Workspaces are fully isolated from each other. No CrewAI — pure LangGraph state machines.

### 4.2 Backend API Design

**POST /api/chat/agency**
```json
{
  "message": "Client A ka progress kya hai?",
  "conversation_id": "abc"
}
→ {
  "response": "Client A pe SEO audit complete, ab content phase mein hai...",
  "workspaces": [{"id": "w1", "name": "Client A", "status": "in_progress"}],
  "conversation_id": "abc"
}
```

**POST /api/chat/workspace/{workspace_id}**
```json
{
  "message": "Client X ke website pe traffic kaise badhau?",
  "conversation_id": "def"
}
→ {
  "response": "Brief SEO agent: audit, keywords, plan...",
  "tasks": [{"agent": "seo", "status": "running", "description": "Keyword research"}],
  "conversation_id": "def"
}
```

Note: Only Ayan/CEO can call this endpoint. Clients do not call APIs directly — they communicate through Ayan or the Agency CEO.

**GET /api/workspaces**
→ List all workspaces with status, last activity, task counts

**GET /api/workspace/{id}**
→ Single workspace detail — agents, tasks, conversation history

**GET /api/workspace/{id}/tasks**
→ All tasks for a workspace with status, assigned agent, results

### 4.3 AgentRouter — Message Routing Logic

```
message comes in → check target path
  ├── /agency          → AgencyCEO.handle_message()
  ├── /workspace/{id}  → WorkspaceManager.get(id).handle_message()
  └── auto (Ayan)      → Agency CEO decides which workspace or handles directly
```

**Agency CEO flow:** Creates tasks, delegates to workspace CEOs via LangGraph state transitions.

**Workspace CEO flow:** Receives brief from Agency CEO, runs multi-phase thinking, delegates to workspace agents via the state graph, compiles response.

**Direct Workspace access (Ayan):** Agency CEO + Workspace Manager give Ayan full visibility into any workspace.

---

## 5. LangGraph State Graph Configuration (Two-Tier)

### 5.1 Agency CEO State Graph

```python
from langgraph.graph import StateGraph, StateNode
from typing import TypedDict, Optional

# ─── AGENCY LEVEL ───────────────────────────────────────

class AgencyState(TypedDict):
    message: str
    conversation_id: str
    thinking_phase: str          # "deconstruct" | "seek" | "envision" | "analyse" | "plan" | "execute"
    thought_output: str
    target_workspace: Optional[str]
    sub_agent_outputs: list
    response: str

class AgencyCEO:
    """
    Single CEO node. Multi-phase strategic thinking, then calls/invokes
    sub-agents or workspace CEOs via tools. Never uses CrewAI.
    """
    
    def __call__(self, state: AgencyState, config) -> dict:
        phase = state["thinking_phase"]
        
        if phase == "deconstruct":
            return self._deconstruct(state)
        elif phase == "seek":
            return self._seek(state)
        elif phase == "envision":
            return self._envision(state, config)
        elif phase == "analyse":
            return self._analyse(state)
        elif phase == "plan":
            return self._plan(state, config)
        elif phase == "execute":
            return self._execute(state, config)
    
    def _deconstruct(self, state: AgencyState) -> dict:
        # Phase 1: Break the problem down
        ...
    def _envision(self, state: AgencyState, config) -> dict:
        # Phase 3: Can call/invoke workspace CEOs or sub-agents here
        # via configured tools (ListWorkspacesTool, GetWorkspaceReportTool, etc.)
        ...

# ─── Build the graph ──────────────────────────────────

def build_agency_graph() -> StateGraph:
    workflow = StateGraph(AgencyState)
    
    workflow.add_node("ceo", AgencyCEO())
    # CEO handles all phases sequentially
    workflow.set_entry_point("ceo")
    workflow.add_edge("ceo", END)
    
    return workflow.compile()
```

### 5.2 Workspace State Graph (Per Client)

```python
# ─── WORKSPACE LEVEL — One graph instance per client ──

class WorkspaceState(TypedDict):
    brief: str                           # CEO's brief (from Agency CEO)
    client_goal: str
    thinking_phase: str
    agent_outputs: dict                  # {"seo": "...", "content": "...", ...}
    consolidated_response: str

class WorkspaceCEONode:
    """
    Workspace CEO — receives brief from Agency CEO, runs multi-phase thinking,
    then calls/invokes each sub-agent (SEO, Content, Website, etc.).
    Clients NEVER talk to this node directly.
    """
    
    def __call__(self, state: WorkspaceState, config) -> dict:
        ...

class SEONode:
    """Receives task from CEO, executes, returns result."""
    ...

class ContentNode:
    """Receives task from CEO, executes, returns result."""
    ...

# ─── Build the workspace graph ────────────────────────

def build_workspace_graph() -> StateGraph:
    workflow = StateGraph(WorkspaceState)
    
    workflow.add_node("ceo", WorkspaceCEONode())
    workflow.add_node("seo", SEONode())
    workflow.add_node("content", ContentNode())
    workflow.add_node("website", WebsiteNode())
    workflow.add_node("analytics", AnalyticsNode())
    
    workflow.set_entry_point("ceo")
    # CEO → all agents in parallel
    workflow.add_edge("ceo", "seo")
    workflow.add_edge("ceo", "content")
    workflow.add_edge("ceo", "website")
    workflow.add_edge("ceo", "analytics")
    # All agents → back to CEO for consolidation
    workflow.add_edge("seo", "ceo")
    workflow.add_edge("content", "ceo")
    workflow.add_edge("website", "ceo")
    workflow.add_edge("analytics", "ceo")
    
    return workflow.compile()
```

### 5.3 WorkspaceManager — Runtime Orchestration

```python
class WorkspaceInstance:
    """A single client's workspace — manages its own LangGraph state graph."""
    
    def __init__(self, ws_id: str, name: str, client_info: dict):
        self.id = ws_id
        self.name = name
        self.client_info = client_info
        self.graph = build_workspace_graph()  # Per-instance compiled graph
        self.state = {}
    
    def handle_brief(self, brief: str, from_agent: str) -> dict:
        """Receive a brief from Agency CEO and run."""
        self.state = {
            "brief": brief,
            "client_goal": self.client_info.get("goal", ""),
            "thinking_phase": "deconstruct",
            "agent_outputs": {},
            "consolidated_response": "",
        }
        result = self.graph.invoke(self.state)
        return result


class WorkspaceManager:
    """Creates and manages per-client workspace instances."""
    
    def __init__(self):
        self.workspaces: dict[str, WorkspaceInstance] = {}
    
    def create_workspace(self, client_name: str, client_info: dict) -> WorkspaceInstance:
        ws_id = f"ws_{len(self.workspaces) + 1:03d}"
        workspace = WorkspaceInstance(
            id=ws_id,
            name=client_name,
            client_info=client_info,
        )
        self.workspaces[ws_id] = workspace
        return workspace
    
    def handle_message(self, workspace_id: str, message: str, user: str) -> dict:
        """Only Ayan/CEO can call this. Clients do not communicate directly."""
        ws = self.workspaces[workspace_id]
        # Workspace CEO processes the brief from Agency CEO
        return ws.handle_brief(message, from_agent=user)
```

### 5.4 Task Creation Flow

Tasks are NOT pre-defined. They are created dynamically via the CEO's multi-phase thinking:

1. **Ayan → Agency CEO:** Agency CEO runs multi-phase thinking (Deconstruct→Seek→Envision→Analyse→Plan→Execute), calls/invokes workspace CEOs with briefs
2. **Agency CEO → Workspace CEO:** Agency CEO calls/invokes a specific workspace CEO with a client brief (SBA — sab kuch about the client)
3. **Workspace CEO:** Runs multi-phase thinking, then calls/invokes sub-agents (SEO, Content, Website, Analytics) via the state graph
4. **Sub-agents** execute tasks autonomously and return results
5. **Workspace CEO** consolidates for the Agency CEO
6. **Agency CEO** reports summary to Ayan

**Clients never communicate with any agent.** All communication is Ayan ↔ CEO ↔ Sub-agents.

---

## 6. SBA Services That Agents Handle

All standard digital marketing agency services:

| Service | Primary Agent | Supporting Agents |
|---------|--------------|-------------------|
| SEO audit & strategy | SEO Agent | Analytics Agent |
| Keyword research | SEO Agent | — |
| Blog writing | Content Agent | SEO Agent (brief) |
| Social media content | Content Agent | — |
| Website design | Website Agent | Content Agent |
| Landing pages | Website Agent | Content Agent, SEO Agent |
| Performance reports | Analytics Agent | All agents |
| Ad copy | Content Agent | — |
| Email newsletters | Content Agent | — |

---

## 7. Frontend Components Needed

**Existing (already in `agency-frontend/src/components/ceo/`):**
- `CEOAgentMonitor.jsx` — Agent status monitor
- `CEODashboardKPIs.jsx` — KPI display
- `CEODecisionLog.jsx` — Decision history log
- `CEOClientList.jsx` — Client list (repurpose as project list)

**Existing chat components:**
- `ChatWindow.jsx` — Agent chat window
- `AgentChat.jsx` — Generic agent chat
- `OrchestratorCard.jsx` — Agent card display

**Needs building:**
- Backend FastAPI server (`/admin/api/`)
- Agent worker that runs LangGraph state graphs
- Database models for tasks/projects
- API routes for chat, agents, tasks

---

## 8. Directory Structure (Proposed)

```
int/
├── agency-frontend/          (existing Next.js app)
│   └── src/
│       ├── app/admin/
│       │   ├── dashboard/    (existing)
│       │   ├── chat/
│       │   │   ├── ceo/      ★ Agency CEO chat
│       │   │   └── workspace/ ★ Per-workspace chat routes
│       │   └── agents/       (existing + workspace-specific routes)
│       └── components/
│           ├── ceo/          (existing)
│           ├── agents/       (existing)
│           └── chat/         (existing)
│
├── admin/                    ★ NEW — Backend service
│   ├── api/
│   │   ├── main.py           FastAPI app
│   │   ├── routes/
│   │   │   ├── agency.py     ★ Agency chat + workspace mgmt
│   │   │   ├── workspace.py  ★ Per-workspace chat + tasks
│   │   │   └── health.py
│   │   └── models/
│   │       ├── schemas.py    Pydantic request/response models
│   │       └── state.py      Workspace + conversation state
│   │
│   ├── agency/
│   │   ├── agency_ceo.py     ★ Agency CEO agent definition
│   │   ├── agency_crew.py    ★ Agency-level crew
│   │   └── workspaces.py     ★ List/manage workspaces
│   │
│   ├── workspace/
│   │   ├── workspace_ceo.py  ★ Workspace CEO agent def
│   │   ├── workspace_crew.py ★ Per-workspace crew builder
│   │   ├── workspace_manager.py ★ Creates/manages instances
│   │   ├── agents/
│   │   │   ├── sba.py
│   │   │   ├── seo.py
│   │   │   ├── content.py
│   │   │   ├── website.py
│   │   │   └── analytics.py
│   │   └── tasks.py          Workspace task templates
│   │
│   ├── tools/
│   │   ├── web_search.py
│   │   ├── workspace_tools.py ★ Workspace management tools
│   │   └── reporting.py
│   │
│   └── requirements.txt
│
├── crewai-repo/              (archived — CrewAI source retained for DelegateWorkTool reference only)
└── ARCHITECTURE.md           (this file)
```

Key structural difference from Phase 1 plan: agency/ and workspace/ are **separate modules**, not one flat list. Each workspace gets its OWN crew at runtime via the WorkspaceManager, not a single shared crew.

---

## 8b. SBA Dedicated Browser (chrome-agent)

Per interview Q14/Q16 (July 10, 2026), SBA Agent requires its own **dedicated real Chrome browser instance** for lead generation — LinkedIn prospecting, freelancer platforms (Upwork, Fiverr), and multi-channel outreach running in parallel (sab ek saath).

| Item | Detail |
|------|--------|
| **Binary** | `chrome-agent/target/release/chrome-agent.exe` |
| **Location** | `C:\Users\TAUSHEF\Downloads\int\chrome-agent\` |
| **Size** | 2,486,272 bytes (release build) |
| **Purpose** | SBA's real browser for CAPTCHA-free, non-headless lead gen |
| **Behavior** | Multi-threaded — handles LinkedIn, Upwork, Fiverr simultaneously |
| **Architecture** | Rust binary that spawns/manages a real Chrome instance |

**Build note:** Requires `C:\tools\llvm-bin` in `$env:PATH` for `dlltool.exe` during cargo build. Append before running `cargo build --release`.

```
$env:PATH = "C:\tools\llvm-bin;$env:PATH"
cargo build --release
```

**Skill dependency:** Referenced in `admin/skills/sba/SKILL.md` line 56 as a prerequisite.

## 9. Key Design Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Process | Hierarchical | CEO delegates, specialists work |
| CEO Agent | Custom manager agent | More control over delegation than auto-generated |
| CEO-to-Workspace Communication | DelegateWorkTool | Agency CEO delegates tasks to workspace CEOs (not direct to agents) |
| Workspace isolation | Per-client Crew instances | Each client's workspace is fully isolated — agents, tasks, data |
| Backend | FastAPI + Python | LangGraph runs in Python, natural fit |
| Frontend | Existing Next.js | Already has admin components |
| Chat paradigm | Message → Route → Crew → Response | Router sends to Agency CEO or specific workspace crew |
| Agent communication | LangGraph state edges + DelegateWorkTool | LangGraph handles CEO → sub-agent orchestration via state graph edges; DelegateWorkTool from archived CrewAI used for cross-workspace CEO-to-CEO delegation |
| Task persistence | SQLite initially | Simple, no infra needed |
| LLM | GPT-4o initially | Best for complex multi-agent reasoning |

---

## 10. Implementation Phases

### Phase 1: Foundation (2-3 days)
- [ ] Set up `admin/` backend with FastAPI
- [ ] Define **all** agents — Agency CEO + Workspace CEO + workspace agents (SBA, SEO, Content, Website, Analytics)
- [ ] Build `WorkspaceManager` — create/manage per-client workspace crews
- [ ] `/api/chat/agency` endpoint → Agency CEO crew
- [ ] `/api/chat/workspace/{id}` endpoint → specific workspace crew

### Phase 2: Agent Capabilities (3-5 days)
- [ ] Add custom tools (web search, file read/write, KeywordResearchTool, etc.)
- [ ] Workspace SEO agent with real keyword research
- [ ] Workspace Content agent with actual writing capabilities
- [ ] Workspace Website agent with code/file modification access
- [ ] Workspace Analytics agent with reporting
- [ ] Agency CEO tools: `ListWorkspacesTool`, `GetWorkspaceReportTool`

### Phase 3: Frontend Integration (2-3 days)
- [ ] Connect Agency CEO chat page (`/admin/chat/ceo`) to `/api/chat/agency`
- [ ] Connect per-workspace chat pages to `/api/chat/workspace/{id}`
- [ ] Dashboard shows all workspaces with status
- [ ] Workspace detail page with agents, tasks, conversation history

### Phase 4: Workspace Lifecycle (1-2 days)
- [ ] CRUD for workspaces — create new client workspace
- [ ] Workspace isolation — verify one client cannot access another's data
- [ ] Workspace CEO reporting to Agency CEO (auto-scheduled or event-driven)
- [ ] Persist conversation state per workspace

### Phase 5: Polish (ongoing)
- [ ] Conversation memory/persistence
- [ ] Agent state persistence across sessions
- [ ] Better error handling
- [ ] EC2 deployment
