# CEO-Centric Agency ("Michael's Office") — Design Spec

**Date:** 2026-08-19
**Branch:** feat/sba-lead-to-meeting-pipeline
**Status:** Approved (user), ready for writing-plans

## Goal

Redesign the agency so the **CEO agent ("Michael") is the single autonomous brain and
the only entry point for the boss (human owner)**. Every other agent (SBA, SEO, Website,
Ads, Content, Social, Analytics) becomes a **worker node that runs ONLY when the CEO
delegates** (possibly via a standing mandate). The frontend becomes a **Munder Difflin /
ai-town style 2D office floor** rendered with **Next.js + PixiJS + Tailwind**, where the
boss talks to the CEO's desk and watches the SBA agent work live on the floor. The
existing Paperclip-derived frontend design is removed. A **generative_agents-style memory /
planning / reflection layer** makes agents feel alive and context-aware.

Reference repos (user-provided, used as design inspiration, NOT copied verbatim):
- github.com/chaitanyagiri/munder-difflin — GOD agent ("Michael") + avatar office floor
- github.com/joonspk-research/generative_agents — memory / planning / reflection
- github.com/get-convex/ai-town — Next.js + PixiJS + Tailwind 2D agent simulation

## Autonomy Model (Option A — strict CEO-gated)

- **Boss → CEO only.** The human owner interacts with exactly one agent: the CEO ("Michael").
  No worker agent is ever directly chatted by the boss.
- **CEO is an autonomous brain.** It thinks for itself (deconstruct → envision → plan →
  execute), proposes/disagrees, and owns outcomes. It understands context: whether a task
  is for the **agency** or for a specific **client workspace** (passed as a `scope` field
  on every delegated task).
- **Workers run only on CEO delegation.** SBA, SEO, Website, Ads, Content, Social,
  Analytics expose a uniform `run_task(task, ctx) -> result` surface. They never self-
  schedule or self-run.
- **Standing mandates (resolves the "SBA must keep working" tension).** The CEO may grant a
  worker a *standing mandate* — e.g. SBA: "run the lead → email → meeting loop forever".
  The worker runs only within that mandate and stops/adjusts when the CEO revokes or
  changes it. This keeps SBA visibly "working" on the floor while remaining CEO-authorized,
  not freelancing. The boss changes strategy by talking to the CEO, who updates mandates.
- **Replaces** the current `admin/agency/agent_loop.py: agent_loop_forever()` (which
  self-schedules SEO/Website/Ads/Analytics) and the free-running 24/7 SBA autopilot. Both
  are brought under the CEO mandate system.

## Backend Architecture

### New / changed modules
- `admin/agency/ceo_controller.py` (**new**) — owns the CEO graph, a command bus, the
  worker registry, and the mandate store. Single source of truth for "what is running".
- `admin/agency/mandates.py` (**new**) — mandate store (SQLite-backed, reusing
  `admin/persistence.py` so it survives restarts):
  `{worker, status: running|paused, standing_task, last_result, scope}`. CEO set/clear.
- `admin/agency/workers.py` (**new**) — uniform worker interface + registry wiring each
  existing specialist agent (SBA, SEO, Website, Ads, Content, Social, Analytics) into
  `run_task(task, ctx)`.
- `admin/agency/agent_loop.py` — refactor `agent_loop_forever()` to a CEO-driven tick:
  it polls CEO mandates and dispatches workers accordingly instead of self-scheduling.
- SBA autopilot (`admin/agency/sba_autopilot.py`) — re-home its lifecycle under the CEO
  mandate system: start/stop/pause controlled by CEO, not a detached forever-task.
- `admin/api/routes/ceo.py` — add `POST /api/ceo/chat` (boss → CEO) and
  `GET /api/ceo/state` (returns CEO + worker statuses + live mandates) plus a WebSocket
  (`/ws/office`) for real-time floor events.
- `admin/api/routes/agent_aliases.py` (`/api/agents/{id}/chat`) — gate behind CEO: direct
  boss-to-worker chat is blocked/redirected to "talk to the CEO".

### CEO context awareness
Every `run_task` / delegate call carries `scope: {kind: "agency"|"client", workspace_id}`
so workers know whether they act for the agency or a specific client. CEO summarizes this
from the boss's message and from SBA handoffs.

## Memory / Planning / Reflection Layer (generative_agents style)

- `admin/agency/memory.py` (**new**) — per-agent memory module with three parts:
  - `memory_stream`: append-only event log (what the agent did/saw).
  - `plan`: current/pending intents (daily or per-mandate).
  - `reflection`: periodic self-summary of recent activity + lessons.
- CEO reflection runs after each pass and produces a short digest for the boss
  (what's running, what's stuck, what to fix). This is the existing digest logic
  (`admin/agency/sba_strategy.py`) generalized to all workers.
- Agents reflect on completed work so subsequent output is contextually better
  (Smallville-style). Memory is file/DB backed and survives restarts.

## Frontend — Office Floor

### Remove Paperclip
- Delete / rewrite Paperclip-derived assets: `agency-frontend/src/app/paperclip.css`,
  Paperclip tokens in `globals.css`, and every component tagged `Paperclip exact` /
  `Source: github.com/paperclipai/...` (e.g. `BreadcrumbBar.js`, `dashboard/org/page.jsx`,
  `dashboard/page.js` metric/agent cards, `dashboard/tickets/page.jsx`, `ActivityCharts.jsx`).
- Establish a new **"Agency Office" design system**: custom Tailwind tokens, no copy-paste
  from Paperclip. Keep the existing tech (Next.js 14 App Router, React 18, Tailwind 3,
  Radix, lucide-react, recharts) and add **PixiJS** for the floor.

### Office floor (PixiJS + Next.js)
- 2D tilemap office. **Desks = workers** (SBA, SEO, Website, Ads, Content, Social,
  Analytics). **CEO = "Michael"** office at center.
- **SBA live work on the floor:** when the SBA mandate is active, its avatar shows a
  "working" state and a desk popup / side panel streams live work — leads found, emails
  sent, replies, meetings booked — driven by the `/ws/office` WebSocket.
- **Boss → CEO chat:** clicking the CEO's desk opens a chat drawer. That is the ONLY active
  chat. Other desks are read-only status views.
- **Envelopes / messages:** a CEO→worker command animates as an envelope flying across the
  floor (Munder Difflin vibe).
- **Agency vs client scope:** UI lets the boss (via the CEO chat) switch context between
  agency-level and a specific client workspace; the floor + chat reflect the chosen scope.

## Real-time Event Bus (WebSocket)
- `GET /ws/office` on the FastAPI backend streams JSON events: agent status changes, SBA
  live work items, CEO thoughts/reflections, mandate changes. Frontend PixiJS floor and
  chat consume these to update live.

## Error Handling & Safety
- Worker errors route to the CEO (`route_error_fix` already exists). CEO either fixes or
  surfaces to the boss. ("Agent mein error hai toh CEO sahi karega.")
- Spend / scope / destructive actions remain behind the boss-approval gate
  (`admin/runtime/spend_policy.py` stays).

## Phasing (implementation order)
1. **Phase 1 — Backend gate.** `ceo_controller.py`, `mandates.py`, `workers.py`, refactor
   `agent_loop_forever`, re-home SBA under CEO, gate direct worker chat. Add tests.
2. **Phase 2 — Memory layer.** `memory.py` (memory/plan/reflection) + CEO reflection digest
   wired into `/api/ceo/state` and the WebSocket.
3. **Phase 3 — Frontend floor.** Remove Paperclip; build PixiJS office + CEO chat +
   SBA live panel + WebSocket client.
4. **Phase 4 — Polish.** Envelopes, avatars, agency/client scope switching in UI.

## Non-goals (YAGNI)
- Not building the full Munder Difflin hive/router/blackboard as a separate process.
- Not changing the Python/FastAPI backend stack or the Next.js frontend stack.
- Not rewriting specialist agent internals (SEO/Ads/etc) — only their gating + memory.
- No new LLM providers.

## Acceptance criteria
- Boss can only reach the CEO; direct worker chat is blocked/redirected.
- SBA shows live work on the office floor while under an active CEO mandate.
- CEO understands and tags agency vs client scope on delegated tasks.
- Every worker has memory/plan/reflection; CEO produces a periodic digest.
- Paperclip design tokens/components are gone from the frontend.
- All existing tests (`npm test`, `npm run lint`) still pass after changes.
