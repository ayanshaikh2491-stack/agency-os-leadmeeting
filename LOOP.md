# Loop Configuration — TAGS Agency OS

This repo uses **loop-engineering** (https://github.com/cobusgreyling/loop-engineering)
as the governance layer for *maintaining the codebase itself* (the `loop-*` tooling,
`LOOP.md`/`STATE.md`/`loop-run-log.md`). A separate, application-layer autonomy system
makes the **agency agents** run themselves — that is documented here.

> Doctor score: **Loop Ready 100 / L3** (`npx @cobusgreyling/loop doctor .`).
> Week-one is report-only for the *coding* loop; the *agency* loop below is L2 (self-scheduled, bounded).

## Agency Autonomy Loops (application layer)

| Loop | Cadence | Level | What it does | Entry point |
|------|---------|-------|--------------|-------------|
| SBA 24/7 Autopilot | 15 min | L2 | Finds leads, cold-emails, books meetings (owner's `store_meetings`), follow-up cadence | `admin/agency/sba_autopilot.py` (own process) |
| Always-on Agent Loop | 60 s tick | L2 | Runs due scheduled tasks (SEO/Website/Ads/Analytics/Analyzing) + auto-provisions client workspaces from SBA handoffs | `admin/agency/agent_loop.py` (`agent_loop_forever`, started in `main.py`) |
| Organic Post Scheduler | 60 s | L2 | Dispatches due social posts | `main.py` `_organic_scheduler_loop` |
| Client-facing Agent Delivery | on-demand | L2/L3 | Client message -> routed to right read/analysis agent -> result returned, no human in loop | `POST /api/store/agent` |

### Autonomy boundary (owner gates preserved)
- SBA autopilot owns live emailing (SMTP cap, business-hours, `SBA_FOLLOWUP_ENABLED` opt-in).
- Agent loop runs **scheduled reports + workspace provisioning only** — never sends email or books meetings itself.
- `POST /api/store/agent` exposes **read/analysis agents only** (seo, content, website, ads, social, analytics, analyzing, memory). SBA / email / meeting agents are explicitly excluded.

## Human Gates
- No auto-fix / no push until review (see `loop-constraints.md`).
- High-risk paths: human review required.
- Mass external actions (follow-up re-email, handoff auto-provision) are owner-opt-in via `.env`.

## Budget
- Max agent-loop tick timeout: 120 s (a stuck task cannot freeze the agency).
- Max tokens/day for coding loop: 100k (see `loop-budget.md`).
- Append each coding-loop run to `loop-run-log.md`.

## Reference
- Loop patterns: https://github.com/cobusgreyling/loop-engineering#patterns
- Design checklist: https://github.com/cobusgreyling/loop-engineering/blob/main/docs/loop-design-checklist.md
- Budget tool: `npx @cobusgreyling/loop-cost --pattern daily-triage`
