# §2 — CEO-Gated On-Demand Execution (Lifecycle & Gating)

**Date:** 2026-08-25
**Status:** Design (to be implemented)
**Depends on:** §1 registry + §3 auto-integration (already built — verify only)
**Reference:** `references/munder-difflin/HIVE.md` + `how-the-god-orchestrator-works.md`
  (local clone, gitignored; read for patterns, do NOT copy code)

---

## 0. Why this spec exists (the gap, proven)

The boss's hard rule (from chat + `docs/specs/2026-08-20-deep-ceo-agent-design.md`):

> Agents must be SMART. CEO runs 24/7 as a listener. Agents sleep by default and
> wake ONLY on CEO command. When a task is done an agent self-sleeps (STANDBY)
> even without an explicit stop. The server must stay light. No 24/7 always-on
> agent loops.

`main.py` boot is already correct: lifespan comment says "No auto worker loop, no
agent_monitor, no organic scheduler — CEO-gated." Good. BUT the following 24/7
loop code is still **alive on disk and dangerous**:

| File | Danger | Evidence |
| --- | --- | --- |
| `admin/agency/sba_autopilot.py` | `run_forever()` ×2 = 24/7 SBA loop | L1311 `async def run_forever`, L1314 `while True`, L1330 `await asyncio.sleep(INTERVAL*60)`; again L1389/L1416 |
| `admin/agency/ceo_monitor.py` | CEO polling `while True` loop | L55 `while True` + `asyncio.sleep(CHECK_INTERVAL_SECONDS)` |
| `admin/agency/sba_monitor.py` | SBA polling loop | (same pattern) |
| `admin/agency/agent_loop.py` | 24/7 scheduled-task tick loop | `_run_loop` / `agent_loop_tick` |

There is **no `LifecycleState`** anywhere (`grep LifecycleState/STANDBY/self_sleep`
→ 0 hits). So the missing piece is a canonical state machine + gating that makes
"agents sleep by default, wake on CEO, self-sleep when done" real and enforced.

---

## 1. Core model (matches Munder Difflin god-orchestrator)

| Munder Difflin | Our §2 |
| --- | --- |
| God agent `desk-ceo`, always-on listener, `isGod` | `CEOController` (Michael) — the ONLY boss-facing agent; 24/7 listener via `POST /api/ceo/chat` (HTTP endpoint, no busy loop = light) |
| Idle agents wake only on **unread inbox** | Agent wakes only when CEO dispatches a brief via `agent_bus.brief_agent(...)` |
| Agent self-sleeps after draining inbox (Stop-hook) | Agent runs `run_once(...)`, reports back, returns to **STANDBY** |
| God = ordinary LLM; **mechanism is dumb plumbing** | CEO = LangGraph agent; routing/state handled by `orchestrator` + `agent_bus` + `LifecycleState` |
| Only critical (destructive/spend/scope/conflict) escalates | CEO delegates; only critical (email send / destructive / spend) surfaces to boss |
| Single-writer registry + message schema w/ `hops` cap | `agent_registry.py` + `agent_bus` (already built) + speech-act messages |

The CEO already exists as `CEOController` (registered in `main.py` lifespan) and
replies to boss chat. We are NOT rebuilding the CEO — we are adding the
**lifecycle gate** around workers so they cannot run 24/7.

---

## 2. LifecycleState (the new thing to build)

A single small module `admin/agency/lifecycle.py`:

```python
from enum import Enum

class LifecycleState(str, Enum):
    STANDBY = "standby"     # default; no process/loop running, cheap
    ACTIVE  = "active"      # CEO dispatched a brief; worker executing run_once
    COOLDOWN = "cooldown"   # just finished; flushing/cleanup; about to STANDBY
    DISABLED = "disabled"   # owner turned this agent off

@dataclass
class AgentRuntime:
    slug: str
    state: LifecycleState = STANDBY
    last_wake: float | None = None
    last_sleep: float | None = None
    current_brief_id: str | None = None
```

Rules (enforced, not advisory):
1. **Default = STANDBY.** At boot, every registered agent is STANDBY. Nothing
   spawns a loop.
2. **Wake = CEO-only.** `Lifecycle.wake(slug, brief_id)` sets ACTIVE and invokes
   the agent's `run_once(...)` executor. Called ONLY by the CEO tool
   (`_tool_delegate` / `_tool_run_sales`), never by a scheduler or monitor.
3. **Self-sleep.** When the executor returns (success or handled-failure), the
   worker calls `Lifecycle.sleep(slug)` → COOLDOWN → STANDBY. No daemon left
   running. Even if the boss never says "stop", the agent sleeps when done.
4. **No `while True`.** Any `run_forever`/monitor loop is deleted or converted to
   a `run_once(...)` that is only ever reached via `Lifecycle.wake`.
5. **Boss can force.** `POST /api/ceo/agent/{slug}/sleep` and `/wake` for manual
   override; stores state in the registry (single-writer, like Munder Difflin).

---

## 3. Gating the existing 24/7 loops (concrete edits)

| File | Action |
| --- | --- |
| `sba_autopilot.py` | Delete `run_forever` (×2). Keep `run_once(workspace_name=...)` as the
  ONLY entry. CEO `_tool_run_sales` calls `SBAAutopilot(ws).run_once()`. |
| `ceo_monitor.py` | Delete `while True` polling. CEO already listens via HTTP
  `/api/ceo/chat`; add a light `GET /api/ceo/state` (no polling loop) for
  introspection only. |
| `sba_monitor.py` | Delete the loop; fold any needed "is SBA done?" check into
  `Lifecycle.sleep` post-condition. |
| `agent_loop.py` | Keep `run_due_tasks` BUT it must only fire inside a CEO mandate
  (boss-scheduled mission), not as a 24/7 tick. Re-label it `run_mandated_tasks`
  and call it from the CEO, not from a background thread. |

Net effect: **zero background loops at runtime.** The only always-on thing is the
FastAPI process (one HTTP server) — that is the "light server" the boss wants.

---

## 4. CEO as the 24/7 listener (already mostly there)

- `POST /api/ceo/chat` — boss → CEO (natural language). CEO reasons, delegates.
- `GET /api/ceo/state` — returns `LifecycleState` of every agent + CEO status.
  Light, on-demand, no polling.
- `GET/POST /api/ceo/agent/{slug}/{wake,sleep}` — manual override.
- CEO tools already exist (`_tool_delegate`, `_tool_run_sales`,
  `_tool_email_client`, `_tool_generate_report`). Make `_tool_delegate` the ONLY
  path that calls `Lifecycle.wake`. This is the "intelligence vs mechanism" split
  from Munder Difflin: CEO (LLM) decides who works; `Lifecycle` (code) enforces
  sleep.

---

## 5. Auto-integration (§3, verify only — already built)

Confirm (don't rebuild): dropping a new agent into `admin/agency/` should
auto-register via `agent_registry.py` and its tools/skills via
`sba_skills.py/seo_skills.py/social_skills.py` + `tools/registry.py` +
`runtime/registry.py`. If a new agent's `run_once` is wired through
`Lifecycle.wake` + `brief_agent`, it self-sleeps for free. External user data
enters via the workspace model already present. **Verification test:** add a
stub 8th agent, confirm it appears in `/api/ceo/state` as STANDBY and can be
woken via CEO without code changes to the orchestrator.

---

## 6. Tests (proof, not jargon)

1. `test_lifecycle_default_standby` — after boot, all 7 agents report STANDBY.
2. `test_wake_only_via_ceo` — calling an agent executor directly raises/is
   blocked unless `Lifecycle.wake` was called by a CEO tool.
3. `test_self_sleep` — after `run_once` returns, agent returns to STANDBY with
   no running loop/task (assert no asyncio task alive for that slug).
4. `test_no_while_true` — grep CI check: `run_forever`/`while True`/`asyncio.run`
   absent from `sba_autopilot.py`, `ceo_monitor.py`, `sba_monitor.py`,
   `agent_loop.py`.
5. `test_new_agent_autointegrate` — stub 8th agent auto-registers STANDBY +
   wakeable via CEO (§3 proof).

---

## 7. Implementation order

1. `admin/agency/lifecycle.py` — `LifecycleState` + `AgentRuntime` + wake/sleep.
2. Gate `sba_autopilot.run_forever` → delete loops, keep `run_once`.
3. Delete `ceo_monitor`/`sba_monitor` loops; add light `/api/ceo/state`.
4. Re-point `agent_loop` to CEO-mandated, not background tick.
5. Wire `_tool_delegate`/`_tool_run_sales` through `Lifecycle.wake`.
6. Add §6 tests. Run `npm test` + targeted pytest.
7. Commit + deploy light, verify `/api/ceo/state` shows all STANDBY.

## 8. What this is NOT

- Not rebuilding the registry (§1) or auto-integration (§3) — already built.
- Not adding a 2D office floor / avatars (that's Munder Difflin's UI; out of
  scope for this server-light backend).
- Not a cloud scheduler / EC2 24/7 worker — explicitly forbidden by boss.
