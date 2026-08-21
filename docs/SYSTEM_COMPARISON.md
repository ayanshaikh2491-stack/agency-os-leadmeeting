# System Comparison — TAGS Agency OS vs Munder Difflin vs Automaton

> Working analysis. Generated during `feat/sba-lead-to-meeting-pipeline` branch work.
> Purpose: deep-read the three repos in this workspace and compare how each is built and runs.

## 1. What we are building — TAGS Agency OS (`int/`)

A digital marketing agency automation system. Each client gets an isolated workspace with a CEO
("Michael") that delegates to sub-agents: SBA, SEO, Content, Website, Ads, Social, Analytics.

- **Stack:** Python FastAPI backend (`:9002`) + Next.js frontend (`:3000`) + SQLite / Supabase.
- **Agent model:** 2-tier hierarchy (Agency CEO → Workspace CEOs → sub-agents). Recent redesign
  (`42e17af`, `cd52596`) moved it to a **single live CEO (Michael)** — no always-on auto-loop, SBA is
  now a CEO tool, and failures return a boss-readable Hindi status.
- **Extra:** SBA owns a real Chrome browser (`chrome-agent` Rust binary) for lead generation.
- **Runs:** `start.bat` → `python -m admin.main` (backend :9002) + `npm run dev` (frontend :3000) →
  open `http://localhost:3000/ceo`.
- **Entry point:** `admin/main.py` (FastAPI app, ~18 route modules).

> **Doc-drift flag:** `ARCHITECTURE.md` and `agent.md` still describe "LangGraph state graph, CrewAI
> banned, parallel sub-agents", but the actual code is single-CEO + raw OpenAI call + no auto-loop.
> These docs need a sync pass.

## 2. Munder Difflin (`_munder/`)

A desktop app that turns the terminal coding CLIs you already run (`claude`, `codex`, `grok`, `agy`,
`kimi`, `qwen`, `opencode`, `crush`, `pi`, `copilot`) into a "office of your clones". Each agent is a
Sims-style avatar on a 2D office floor.

- **Stack:** Electron + React + TypeScript + Pixi.js + xterm.js + node-pty.
- **Two data planes:**
  - *Terminal plane:* each agent is a real `node-pty` process, rendered with xterm.js.
  - *Event plane:* Claude Code hooks (`PreToolUse`, `PostToolUse`, `Stop`, ...) POST JSON to a hook
    server; the hive router delivers messages between agent mailboxes.
- **Hive:** per-agent markdown memory + semantic recall index, atomic-file mailboxes, shared
  blackboard, append-only event log, single-committer git (avoids `index.lock` corruption).
- **Orchestrator:** GOD agent = **Michael** (your clone, boss of the floor). Routes, adjudicates,
  escalates only critical items (spend, scope, destructive) to you.
- **Safety:** human gates + circuit breaker (steer → constrain → stop).
- **Project structure:**
  ```
  src/main/    → pty.ts, hive.ts, hooks.ts, memory.ts, config.ts, transcript.ts,
                 telemetry.ts, breaker.ts, control.ts, reflect.ts, db.ts, github.ts,
                 fs.ts, git.ts
  src/preload/ → window.cth (typed IPC bridge)
  src/renderer/→ OfficeFloor (Pixi.js), CommandCenter, TasksKanban, ThreadsPanel,
                 ToolWaterfall, scene/office/*
  ```
- **Runs:** `npm install && npm run dev` (Electron app, not a server).

## 3. Automaton (`_vendor_automaton/`, Conway-Research/automaton)

A self-improving, self-replicating, sovereign AI that earns its own compute. Runs a continuous
Think → Act → Observe loop, generates an Ethereum wallet at boot, and pays for itself via Conway
Cloud (x402 stablecoin payments). Survival tiers (normal / low_compute / critical / dead) driven by
credit balance. Writes a self-authored `SOUL.md`; self-modifies (audit-logged, git-versioned) within
a 3-law constitution; replicates children with tracked lineage.

- **Stack:** TypeScript (pnpm monorepo) + Ethereum wallet + x402 + ERC-8004 identity + Conway Cloud
  (RL-trained internally, per README).
- **Runs:** `node dist/index.js --run` (interactive setup wizard on first boot).

## 4. Comparison matrix

| Dimension | TAGS Agency OS (ours) | Munder Difflin | Automaton (Conway) |
|---|---|---|---|
| Purpose | Marketing agency automation (lead→meeting, SEO, content) | Visualize/coordinate your coding agents | Self-earning, self-replicating sovereign AI |
| Type | Business SaaS backend + web UI | Desktop dev harness (Electron) | Standalone AI runtime (Node, Conway Cloud) |
| Stack | Python FastAPI + Next.js + SQLite/Supabase | Electron + React + Pixi.js + node-pty | TypeScript + ETH wallet + x402 + RL |
| Orchestrator | CEO "Michael" (single, CEO-gated) | GOD agent "Michael" (your clone) | Single ReAct loop, SOUL.md |
| Agents | Business sub-agents (SBA, SEO, Ads...) | Real terminal CLIs as avatars | Itself + replicated children |
| Visualization | `/ceo` control room (web) | 2D office floor, avatars walk to stations | CLI + status (no floor) |
| Memory | Per-agent memory + mandates | Markdown memory + semantic palace | SQLite + git-versioned self-mod |
| Human control | CEO gate + Hindi failure fallback | Human gates + circuit breaker | 3-law constitution + creator audit |
| Runs via | `start.bat` → 2 servers | `npm run dev` (Electron) | `node dist/index.js --run` |
| Domain | Marketing / business | Generic coding | AI existential experiment |

## 5. Key overlap

**"Michael" appears in two systems.** Our CEO Michael and Munder's GOD agent Michael share the same
pattern: one boss agent that runs the floor/agency, handles routine work itself, and escalates only
critical decisions to a human. TAGS Agency OS is essentially the business-domain version of Munder's
harness — marketing sub-agents instead of coding CLIs.

## 6. Possible next steps

1. Borrow Munder's hive/mailbox/router pattern into our `/ceo` control room.
2. Borrow Munder's floor visualization (avatar-walks-to-station) for live agent status.
3. Sync drifted `ARCHITECTURE.md` / `agent.md` with the actual single-CEO code.
