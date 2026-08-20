# Deep CEO Agent Design — Munder-Difflin Agency OS

**Date:** 2026-08-20
**Status:** Design (to be implemented)
**Supersedes:** 2026-08-20-single-agent-ceo-backend-design.md (crash fix only)

## Core Model (decided)

The agency is a **boss + workers** org, exactly like Munder-Difflin:

- **CEO Michael = the ONLY boss-facing agent.** The owner ("Michael"/boss) talks
  ONLY to the CEO. Workers never speak to the boss directly (enforced by the 426
  gate on `/api/agents/{slug}/chat`).
- **CEO instructs agents; agents execute.** The CEO is a LangGraph reasoning
  agent. It does NOT do the grunt work itself — it **delegates** by sending
  briefs to specialist agents over the existing inter-agent message bus
  (`admin.workspace.agent_bus.brief_agent`). Agents pick up the brief and run.
- **SBA is NOT a separate auto-running service.** The old always-on SBA loop,
  `agent_monitor`, and `organic_scheduler` are removed (done in prior commit).
  Instead, **SBA is one of the CEO's worker tools**: when the boss asks the CEO
  to find leads / run sales for a client, the CEO dispatches a brief to the SBA
  worker, which executes lead-finding + email for that workspace. No background
  loop — purely CEO-triggered, on-demand, per-workspace.

## How the pieces talk (communication)

1. **Boss -> CEO:** `POST /api/ceo/chat` (natural language). CEO reasons, may
   call tools, returns a reply + thinking phases.
2. **CEO -> Agent:** `brief_agent(from_agent="ceo", to_agent=<slug>,
   workspace_id, task, context)`. This writes to the in-memory + SQLite agent
   message bus (`agent_messages` table). The CEO's reply to the boss summarizes
   what it told the agent to do.
3. **Agent -> work:** Each worker has a real executor:
   - SBA worker -> `SBAAutopilot(workspace_name=ws).run_once()` (lead find +
     email via the email client).
   - Content/SEO/etc. -> their LangGraph agents (already implemented).
   The CEO triggers the worker's executor; the worker runs and reports back via
   `respond_to_brief` on the bus.
4. **Agent -> Boss:** only through the CEO. The CEO reads agent replies from the
   bus and surfaces them to the boss in the next chat / control-room digest.

## CEO capabilities (tools)

The CEO graph (`admin/agency/ceo.py`) already has tools
(`_tool_delegate`, `_tool_parallel_blast`, `_tool_receive_handoff`,
`_tool_generate_report`, etc.). In the deep design these are made REAL:

- **`_tool_delegate(worker, task, workspace)`** — sends a brief to a worker over
  the bus AND triggers that worker's executor (so the work actually happens, not
  just a message). Returns what the worker produced.
- **`_tool_run_sales(workspace)`** — CEO's sales move: instantiate the SBA worker
  for that workspace and run one pass (find leads + queue emails). Wrapped in
  try/except; on failure returns a clear status.
- **`_tool_email_client(workspace, to, subject, body)`** — queue an email to a
  client (see Email below).
- **`_tool_generate_report(...)`** — already aggregates workspace/lead data into
  a report for the boss.

## Email (decision D — queue now, real later)

- New `admin/tools/email_queue.py` with `QueuedEmailClient` implementing the SAME
  `send_email(to, subject, body, cc_owner)` interface as `SBAEmailClient`.
- Instead of SMTP, it appends to an outbound `email_outbox` table (SQLite) and
  returns `True`. Every queued email is auditable (to/subject/body/timestamp/
  workspace/status=pending).
- `SBAAutopilot` already accepts an `email_client` arg, so wiring the queued
  client requires NO change inside SBA — we just pass `QueuedEmailClient()` when
  constructing it from the CEO tool.
- Later, flipping to real email = swap the client to `SBAEmailClient` (env
  creds) — zero SBA code change.
- New endpoints: `GET /api/ceo/email/outbox` (boss sees queued emails),
  `POST /api/ceo/email/send` (queue one now).

## Per-workspace behavior (how CEO thinks per workspace)

- At chat time the CEO builds workspace context (`_build_workspace_context`)
  which lists every workspace, its client, agents, and lead counts.
- When the boss names a client/workspace, the CEO scopes the brief + SBA run to
  that `workspace_id` (the `route_to_agent` / `SBAAutopilot(workspace_name=)`
  already scope by workspace).
- Each workspace has its OWN email identity isolation (already enforced in
  `build_workspace_email_client`) so the agency never emails from a client's
  inbox.

## Failure fallback (what CEO does if an agent breaks)

- Every CEO tool is wrapped in try/except. On failure the tool returns a clear,
  boss-readable Hindi/English status, e.g.
  "Bhai, SBA fail ho gaya workspace X ke liye: <reason>. Lead save ho gaya but
  email queue nahi hua. Baad mein retry karo ya mujhe bolo."
- The top-level `CEO.chat()` already has a catch that returns a graceful Hindi
  message if the whole graph blows up.
- Failed emails stay in the outbox with `status=failed` + error, so they are
  visible and retryable from the control room — never silently dropped.

## Reports & where they show up

- **Control Room (Munder-Difflin floor):** `/api/ceo/state` shows CEO status +
  worker list + floor activity (live agent_activity log). `/api/ceo/ws/office`
  websocket streams it.
- **Digest:** `/api/ceo/digest` returns a text summary of mandates/activity.
- **Boss chat:** the CEO's reply always summarizes what it did / delegated.
- **Email outbox:** `/api/ceo/email/outbox` shows everything queued to clients.

## Frontend contract

All existing `/api/ceo/*` endpoints stay. New: `/api/ceo/email/outbox`,
`/api/ceo/email/send`. The Munder-Difflin floor renders the CEO node + floor
activity (already wired to `/api/ceo/ws/office`).

## Implementation steps

1. `admin/tools/email_queue.py` — `QueuedEmailClient` + `email_outbox` table
   (init in persistence), `list_outbox()`, `queue_email()`, `mark_sent/failed()`.
2. CEO tool `_tool_run_sales(workspace)` + make `_tool_delegate` trigger the
   worker executor (SBA run_once for sba; existing route_to_agent for others).
3. `admin/api/routes/ceo.py` — add `/email/outbox` + `/email/send`; wire
   `_tool_email_client`.
4. Failure fallback text in each new tool.
5. Spec commit + deploy to EC2 + verify (`/api/ceo/state`, email outbox, 426).

## Verification

- `python -c "import admin.main"` -> IMPORT_OK
- Live: `/api/ceo/state` shape ok; `POST /api/ceo/email/send` queues an email
  (visible in `/api/ceo/email/outbox`); `POST /api/agents/sba/chat` -> 426.
