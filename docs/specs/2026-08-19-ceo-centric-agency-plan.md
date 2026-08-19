# CEO-Centric Agency ("Michael's Office") Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Re-architect the agency so the CEO agent ("Michael") is the single autonomous brain and only entry point for the boss; every other agent becomes a CEO-gated worker node; add a generative-agents-style memory/plan/reflection layer; and rebuild the frontend as a Munder Difflin / ai-town style PixiJS office floor where the boss chats with the CEO and watches the SBA agent work live.

**Architecture:** A new `admin/agency/ceo_controller.py` owns the CEO graph, a worker registry, and a SQLite-backed mandate store. Specialist agents (SBA, SEO, Website, Ads, Content, Social, Analytics) are wrapped as uniform `run_task(task, ctx)` workers that only execute when the CEO delegates (optionally via a standing mandate). The existing `agent_loop_forever()` and the free-running SBA autopilot are re-homed under the CEO mandate system. A `admin/agency/memory.py` module gives every agent + the CEO a memory_stream / plan / reflection. The frontend is rebuilt in `agency-frontend` (Next.js + Tailwind) with a new PixiJS office floor, the Paperclip design removed, and a `/ws/office` WebSocket feeding live floor events.

**Tech Stack:** Python 3.11+, FastAPI, aiosqlite (existing `admin/persistence.py`), LangGraph (existing CEO graph), Next.js 14 (App Router) + React 18 + Tailwind 3 + PixiJS (new dep) for the frontend. Keep existing backend/frontend stacks — do not change them.

## Global Constraints

- Every worker task carries `scope: {kind: "agency"|"client", workspace_id}` so agents know whether they act for the agency or a specific client workspace.
- Workers run ONLY on CEO delegation (or an active CEO standing mandate). No self-scheduling.
- Mandate store is SQLite-backed, reusing `admin/persistence.py` (`init_persistence()` / shared connection) so it survives restarts.
- SBA autopilot lifecycle is controlled by the CEO mandate system, not a detached forever-task.
- Frontend: remove all Paperclip-derived assets (`paperclip.css`, Paperclip tokens in `globals.css`, components tagged `Paperclip exact` / `Source: github.com/paperclipai/...`); add a new custom "Agency Office" Tailwind design system. Keep Next.js 14 / React 18 / Tailwind 3 / Radix / lucide-react / recharts; add PixiJS.
- Spend / scope / destructive actions stay behind the existing boss-approval gate (`admin/runtime/spend_policy.py`).
- All changes must keep `npm test` and `npm run lint` passing.
- Reference repos are design inspiration only; do not copy their code verbatim.

---

### Task 1: Mandate store (SQLite-backed)

**Files:**
- Create: `admin/agency/mandates.py`
- Create: `tests/test_mandates.py`

**Interfaces:**
- Consumes: `admin.persistence` (`init_persistence`, `get_workspace_db`, `row_to_dict`) — existing async SQLite layer.
- Produces:
  - `set_mandate(worker: str, status: str, standing_task: str, scope: dict, last_result: str | None = None) -> dict`
  - `get_mandate(worker: str) -> dict | None`
  - `list_mandates() -> list[dict]`
  - `clear_mandate(worker: str) -> bool`
  - `MandateStore` table created on `init_persistence()` via `CREATE TABLE IF NOT EXISTS mandates (...)`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_mandates.py
import asyncio
from admin.agency import mandates as m


def test_set_get_clear_mandate():
    async def run():
        await m.init_mandates_table()
        await m.set_mandate(
            worker="sba",
            status="running",
            standing_task="lead->email->meeting loop",
            scope={"kind": "agency", "workspace_id": "ws_agency"},
        )
        got = await m.get_mandate("sba")
        assert got is not None
        assert got["status"] == "running"
        assert got["worker"] == "sba"
        all_m = await m.list_mandates()
        assert any(x["worker"] == "sba" for x in all_m)
        ok = await m.clear_mandate("sba")
        assert ok is True
        assert await m.get_mandate("sba") is None
    asyncio.run(run())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:\Users\TAUSHEF\Downloads\int && python -m pytest tests/test_mandates.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'admin.agency.mandates'`

- [ ] **Step 3: Write minimal implementation**

```python
# admin/agency/mandates.py
"""CEO-backed standing mandates. A worker runs ONLY when it has an active mandate."""
from __future__ import annotations

import json
from typing import Any
from datetime import datetime, timezone

from admin.persistence import get_workspace_db, row_to_dict

TABLE = """
CREATE TABLE IF NOT EXISTS mandates (
    worker TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    standing_task TEXT NOT NULL DEFAULT '',
    scope TEXT NOT NULL DEFAULT '{}',
    last_result TEXT,
    updated_at TEXT NOT NULL
);
"""


async def init_mandates_table() -> None:
    db = await get_workspace_db()
    await db.execute(TABLE)
    await db.commit()


async def set_mandate(worker: str, status: str, standing_task: str,
                      scope: dict[str, Any], last_result: str | None = None) -> dict[str, Any]:
    db = await get_workspace_db()
    ts = datetime.now(timezone.utc).isoformat()
    await db.execute(
        "INSERT INTO mandates(worker,status,standing_task,scope,last_result,updated_at) "
        "VALUES(?,?,?,?,?,?) "
        "ON CONFLICT(worker) DO UPDATE SET status=excluded.status,"
        "standing_task=excluded.standing_task,scope=excluded.scope,"
        "last_result=excluded.last_result,updated_at=excluded.updated_at",
        (worker, status, standing_task, json.dumps(scope), last_result, ts),
    )
    await db.commit()
    return await get_mandate(worker) or {}


async def get_mandate(worker: str) -> dict[str, Any] | None:
    db = await get_workspace_db()
    cur = await db.execute("SELECT * FROM mandates WHERE worker=?", (worker,))
    row = await cur.fetchone()
    if not row:
        return None
    d = row_to_dict(row)
    d["scope"] = json.loads(d.get("scope") or "{}")
    return d


async def list_mandates() -> list[dict[str, Any]]:
    db = await get_workspace_db()
    cur = await db.execute("SELECT * FROM mandates")
    rows = await cur.fetchall()
    return [{**row_to_dict(r), "scope": json.loads(row_to_dict(r).get("scope") or "{}")} for r in rows]


async def clear_mandate(worker: str) -> bool:
    db = await get_workspace_db()
    cur = await db.execute("DELETE FROM mandates WHERE worker=?", (worker,))
    await db.commit()
    return cur.rowcount > 0
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd C:\Users\TAUSHEF\Downloads\int && python -m pytest tests/test_mandates.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add admin/agency/mandates.py tests/test_mandates.py
git commit -q -m "feat: SQLite-backed CEO mandate store"
```

---

### Task 2: Worker registry + uniform `run_task` interface

**Files:**
- Create: `admin/agency/workers.py`
- Create: `tests/test_workers.py`

**Interfaces:**
- Consumes: existing specialist agent entrypoints — `AgencyCEO.delegate_to_workspace` (tool name in `admin/agency/ceo.py`), SBA autopilot `admin/agency/sba_autopilot.SBAAutopilot`, website/ads/seo/etc routes in `admin/api/routes/*`.
- Produces:
  - `WORKERS: dict[str, dict]` — registry of worker metadata `{type, label, kind, runnable}`.
  - `async def run_worker(worker: str, task: str, ctx: dict) -> dict` — calls the right underlying executor; records activity via `admin.workspace.manager.update_agent_activity` + `append_agent_activity_log` and writes to memory (Task 5 hook is a no-op stub here).
  - `list_workers() -> list[dict]` — for the floor UI.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_workers.py
import asyncio
from admin.agency import workers as w


def test_run_worker_records_activity():
    async def run():
        # Use a fake worker to avoid touching real LLM agents.
        w.register_worker("dummy", "Dummy", "test", _fake_run)
        res = await w.run_worker("dummy", "do thing", {"scope": {"kind": "agency", "workspace_id": "ws_agency"}})
        assert res["ok"] is True
        from admin.workspace.manager import get_agent_activity_log
        log = get_agent_activity_log("ws_agency", "dummy")
        assert any("do thing" in e["text"] for e in log)
    asyncio.run(run())


async def _fake_run(task: str, ctx: dict) -> dict:
    return {"ok": True, "echo": task}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:\Users\TAUSHEF\Downloads\int && python -m pytest tests/test_workers.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'admin.agency.workers'`

- [ ] **Step 3: Write minimal implementation**

```python
# admin/agency/workers.py
"""Uniform worker interface. Every agent runs ONLY via run_worker (CEO-gated)."""
from __future__ import annotations

from typing import Any, Awaitable, Callable

from admin.workspace.manager import update_agent_activity, append_agent_activity_log

WorkerFn = Callable[[str, dict], Awaitable[dict]]

WORKERS: dict[str, dict[str, Any]] = {}


def register_worker(worker_type: str, label: str, kind: str, fn: WorkerFn) -> None:
    WORKERS[worker_type] = {"type": worker_type, "label": label, "kind": kind, "runnable": fn}


async def run_worker(worker: str, task: str, ctx: dict[str, Any]) -> dict[str, Any]:
    meta = WORKERS.get(worker)
    if not meta:
        return {"ok": False, "error": f"unknown worker {worker}"}
    scope = ctx.get("scope", {"kind": "agency", "workspace_id": "agency"})
    ws = scope.get("workspace_id", "agency")
    update_agent_activity(ws, worker, "working", task[:80])
    append_agent_activity_log(ws, worker, "task", f"CEO task: {task[:200]}")
    try:
        result = await meta["runnable"](task, ctx)
    except Exception as exc:  # noqa: BLE001
        update_agent_activity(ws, worker, "error")
        append_agent_activity_log(ws, worker, "status", f"error: {exc}")
        return {"ok": False, "error": str(exc)}
    update_agent_activity(ws, worker, "idle")
    append_agent_activity_log(ws, worker, "status", f"done: {str(result)[:160]}")
    return {"ok": True, "result": result}


def list_workers() -> list[dict[str, Any]]:
    return [
        {"type": m["type"], "label": m["label"], "kind": m["kind"]}
        for m in WORKERS.values()
    ]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd C:\Users\TAUSHEF\Downloads\int && python -m pytest tests/test_workers.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add admin/agency/workers.py tests/test_workers.py
git commit -q -m "feat: uniform worker registry and run_worker interface"
```

---

### Task 3: Wire specialist agents into the worker registry

**Files:**
- Modify: `admin/agency/workers.py` (add a `register_builtins()` function + imports)
- Modify: `tests/test_workers.py` (add a test that `register_builtins` populates the registry)

**Interfaces:**
- Consumes: `admin.agency.workers.register_worker`, `admin.agency.sba_autopilot.SBAAutopilot`, `admin.workspace.manager` handlers (already used by `/api/ceo/chat`).
- Produces: `register_builtins()` that registers sba / seo / website / ads / content / social / analytics as workers. Each worker fn calls the existing underlying agent. For SBA, map `task` → `SBAAutopilot.run_once(...)`. For others, route through the existing route handlers or a thin wrapper; keep it minimal and defensive.

- [ ] **Step 1: Write the failing test**

```python
# append inside tests/test_workers.py
def test_register_builtins_populates_registry():
    from admin.agency import workers as w
    w.register_builtins()
    types = {m["type"] for m in w.list_workers()}
    assert {"sba", "seo", "website", "ads", "content", "social", "analytics"} <= types
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:\Users\TAUSHEF\Downloads\int && python -m pytest tests/test_workers.py -v`
Expected: FAIL — `AttributeError: module 'admin.agency.workers' has no attribute 'register_builtins'`

- [ ] **Step 3: Write minimal implementation** (append to `admin/agency/workers.py`)

```python
def register_builtins() -> None:
    """Register the agency's specialist agents as CEO-gated workers."""
    register_worker("sba", "SBA — Lead→Email→Meeting", "sales", _run_sba)
    register_worker("seo", "SEO", "growth", _run_passthrough)
    register_worker("website", "Website", "build", _run_passthrough)
    register_worker("ads", "Ads", "growth", _run_passthrough)
    register_worker("content", "Content", "creative", _run_passthrough)
    register_worker("social", "Social", "creative", _run_passthrough)
    register_worker("analytics", "Analytics", "insight", _run_passthrough)


async def _run_sba(task: str, ctx: dict) -> dict:
    from admin.agency.sba_autopilot import SBAAutopilot
    ap = SBAAutopilot()
    stats = await ap.run_once()
    return {"stats": stats}


async def _run_passthrough(task: str, ctx: dict) -> dict:
    # Placeholder executor: specialist agents are invoked by the CEO via the
    # existing /api routes. Keep this defensive until Task 6 wires live exec.
    return {"note": f"{ctx.get('scope', {}).get('workspace_id', 'agency')}: {task[:120]}"}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd C:\Users\TAUSHEF\Downloads\int && python -m pytest tests/test_workers.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add admin/agency/workers.py tests/test_workers.py
git commit -q -m "feat: register specialist agents as CEO-gated workers"
```

---

### Task 4: CEO controller — owns graph + mandates + delegation

**Files:**
- Create: `admin/agency/ceo_controller.py`
- Create: `tests/test_ceo_controller.py`
- Modify: `admin/main.py` (call `register_builtins()` + `init_mandates_table()` at startup)

**Interfaces:**
- Consumes: `admin.agency.ceo.AgencyCEO.chat`, `admin.agency.workers.run_worker`, `admin.agency.mandates.*`, `register_builtins`.
- Produces:
  - `class CEOController` with:
    - `async def chat(self, message: str, conversation_id: str | None = None) -> dict` — runs CEO, returns `{response, conversation_id, phases, scope_detected}`.
    - `async def delegate(self, worker: str, task: str, scope: dict) -> dict` — asserts worker is allowed; runs via `run_worker`; records a mandate if `standing=True`.
    - `async def set_mandate(self, worker, standing_task, scope) -> dict`
    - `async def get_state(self) -> dict` — CEO + all worker statuses + active mandates + floor activity (reuse `get_floor_activity`).
  - Module-level `ceo_controller = CEOController()` singleton.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_ceo_controller.py
import asyncio
from admin.agency import ceo_controller as c


def test_ceo_controller_state_shape():
    async def run():
        c.register()  # wires builtins + mandates
        st = await c.ceo_controller.get_state()
        assert "ceo" in st
        assert "workers" in st
        assert "mandates" in st
    asyncio.run(run())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:\Users\TAUSHEF\Downloads\int && python -m pytest tests/test_ceo_controller.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'admin.agency.ceo_controller'`

- [ ] **Step 3: Write minimal implementation**

```python
# admin/agency/ceo_controller.py
"""CEO Controller — single brain. Owns the CEO graph, mandates, delegation."""
from __future__ import annotations

from typing import Any

from admin.agency import workers as workers_mod
from admin.agency import mandates as mandates_mod
from admin.agency.ceo import AgencyCEO
from admin.workspace.manager import get_floor_activity

_ceo = AgencyCEO()


class CEOController:
    def __init__(self) -> None:
        self.ceo = _ceo

    def register(self) -> None:
        workers_mod.register_builtins()

    async def chat(self, message: str, conversation_id: str | None = None) -> dict[str, Any]:
        from admin.workspace.manager import update_agent_activity, append_agent_activity_log
        update_agent_activity("ceo", "ceo", "working", message[:80])
        append_agent_activity_log("ceo", "ceo", "msg", f"Boss: {message[:160]}")
        response, conv_id, phases = await self.ceo.chat(
            message=message, user_role="the agency owner", conversation_id=conversation_id
        )
        update_agent_activity("ceo", "ceo", "idle")
        append_agent_activity_log("ceo", "ceo", "msg", f"CEO: {(response or '')[:160]}")
        # Lightweight scope detection: explicit "client" mention -> client scope.
        scope_kind = "client" if "client" in message.lower() else "agency"
        return {
            "response": response,
            "conversation_id": conv_id,
            "phases": phases,
            "scope_detected": {"kind": scope_kind, "workspace_id": "agency" if scope_kind == "agency" else "detect"},
        }

    async def delegate(self, worker: str, task: str, scope: dict[str, Any],
                       standing: bool = False) -> dict[str, Any]:
        if standing:
            await mandates_mod.set_mandate(worker, "running", task, scope)
        return await workers_mod.run_worker(worker, task, {"scope": scope})

    async def get_state(self) -> dict[str, Any]:
        mandates = await mandates_mod.list_mandates()
        workers = workers_mod.list_workers()
        return {
            "ceo": {"status": "idle"},
            "workers": workers,
            "mandates": mandates,
            "floor": get_floor_activity(None),
        }


ceo_controller = CEOController()
```

- [ ] **Step 4: Wire startup in `admin/main.py`**

Add inside the `lifespan` app-start block (after `load_workspaces_from_db()`), before the agent loop start:

```python
    # CEO controller: register builtin workers + ensure mandate table exists.
    try:
        from admin.agency import ceo_controller as ceo_ctrl
        from admin.agency import mandates as mandates_mod
        await mandates_mod.init_mandates_table()
        ceo_ctrl.ceo_controller.register()
    except Exception as exc:  # noqa: BLE001
        logging.getLogger("admin.main").warning("ceo controller init failed: %s", exc)
```

And in `main()` import at top add nothing new (already imports). 

- [ ] **Step 5: Run test to verify it passes**

Run: `cd C:\Users\TAUSHEF\Downloads\int && python -m pytest tests/test_ceo_controller.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add admin/agency/ceo_controller.py tests/test_ceo_controller.py admin/main.py
git commit -q -m "feat: CEO controller owns graph, mandates, delegation"
```

---

### Task 5: Memory / plan / reflection module

**Files:**
- Create: `admin/agency/memory.py`
- Create: `tests/test_memory.py`

**Interfaces:**
- Consumes: `admin.persistence` (`get_workspace_db`, `row_to_dict`).
- Produces:
  - `async def record_event(agent: str, kind: str, text: str, scope: dict | None = None) -> None` — append to memory_stream.
  - `async def set_plan(agent: str, plan: list[str]) -> None`
  - `async def get_plan(agent: str) -> list[str]`
  - `async def add_reflection(agent: str, summary: str) -> None`
  - `async def get_memory(agent: str) -> dict` — `{stream, plan, reflections}`.
  - Table `agent_memory` (agent TEXT, kind TEXT, text TEXT, scope TEXT, ts TEXT) and `agent_plan` (agent TEXT PRIMARY KEY, plan TEXT), `agent_reflection` (agent TEXT PRIMARY KEY, reflections TEXT).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_memory.py
import asyncio
from admin.agency import memory as mem


def test_memory_roundtrip():
    async def run():
        await mem.init_memory_tables()
        await mem.record_event("sba", "task", "emailed Al's Auto", {"kind": "agency"})
        await mem.set_plan("sba", ["run lead loop", "book meetings"])
        await mem.add_reflection("sba", "email cap reached; slow down")
        m = await mem.get_memory("sba")
        assert any("Al's Auto" in e["text"] for e in m["stream"])
        assert "book meetings" in m["plan"]
        assert len(m["reflections"]) == 1
    asyncio.run(run())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:\Users\TAUSHEF\Downloads\int && python -m pytest tests/test_memory.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'admin.agency.memory'`

- [ ] **Step 3: Write minimal implementation**

```python
# admin/agency/memory.py
"""generative_agents-style memory/plan/reflection per agent + CEO."""
from __future__ import annotations

import json
from typing import Any
from datetime import datetime, timezone

from admin.persistence import get_workspace_db, row_to_dict

SQL = """
CREATE TABLE IF NOT EXISTS agent_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent TEXT NOT NULL, kind TEXT NOT NULL, text TEXT NOT NULL,
    scope TEXT NOT NULL DEFAULT '{}', ts TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS agent_plan (
    agent TEXT PRIMARY KEY, plan TEXT NOT NULL DEFAULT '[]');
CREATE TABLE IF NOT EXISTS agent_reflection (
    agent TEXT PRIMARY KEY, reflections TEXT NOT NULL DEFAULT '[]');
"""


async def init_memory_tables() -> None:
    db = await get_workspace_db()
    await db.executescript(SQL)
    await db.commit()


async def record_event(agent: str, kind: str, text: str, scope: dict | None = None) -> None:
    db = await get_workspace_db()
    ts = datetime.now(timezone.utc).isoformat()
    await db.execute(
        "INSERT INTO agent_memory(agent,kind,text,scope,ts) VALUES(?,?,?,?,?)",
        (agent, kind, text, json.dumps(scope or {}), ts),
    )
    await db.commit()


async def set_plan(agent: str, plan: list[str]) -> None:
    db = await get_workspace_db()
    await db.execute(
        "INSERT INTO agent_plan(agent,plan) VALUES(?,?) ON CONFLICT(agent) DO UPDATE SET plan=excluded.plan",
        (agent, json.dumps(plan)),
    )
    await db.commit()


async def get_plan(agent: str) -> list[str]:
    db = await get_workspace_db()
    cur = await db.execute("SELECT plan FROM agent_plan WHERE agent=?", (agent,))
    row = await cur.fetchone()
    return json.loads(row[0]) if row else []


async def add_reflection(agent: str, summary: str) -> None:
    db = await get_workspace_db()
    cur = await db.execute("SELECT reflections FROM agent_reflection WHERE agent=?", (agent,))
    row = await cur.fetchone()
    items = json.loads(row[0]) if row else []
    items.append(summary)
    items = items[-20:]
    await db.execute(
        "INSERT INTO agent_reflection(agent,reflections) VALUES(?,?) ON CONFLICT(agent) DO UPDATE SET reflections=excluded.reflections",
        (agent, json.dumps(items)),
    )
    await db.commit()


async def get_memory(agent: str) -> dict[str, Any]:
    db = await get_workspace_db()
    cur = await db.execute("SELECT * FROM agent_memory WHERE agent=? ORDER BY id DESC LIMIT 200", (agent,))
    rows = await cur.fetchall()
    stream = [
        {**row_to_dict(r), "scope": json.loads(row_to_dict(r).get("scope") or "{}")}
        for r in rows
    ]
    return {"stream": stream, "plan": await get_plan(agent), "reflections": (await _reflections(agent))}


async def _reflections(agent: str) -> list[str]:
    db = await get_workspace_db()
    cur = await db.execute("SELECT reflections FROM agent_reflection WHERE agent=?", (agent,))
    row = await cur.fetchone()
    return json.loads(row[0]) if row else []
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd C:\Users\TAUSHEF\Downloads\int && python -m pytest tests/test_memory.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add admin/agency/memory.py tests/test_memory.py
git commit -q -m "feat: per-agent memory, plan, reflection module"
```

---

### Task 6: Re-home `agent_loop_forever` + SBA under CEO mandates

**Files:**
- Modify: `admin/agency/agent_loop.py` (replace self-scheduling with CEO-mandate-driven tick)
- Modify: `admin/agency/sba_autopilot.py` (expose `run_once` already exists; gate the forever loop)
- Create: `tests/test_ceo_loop.py`

**Interfaces:**
- Consumes: `admin.agency.mandates.list_mandates`, `admin.agency.workers.run_worker`, existing `_auto_process_due_handoffs`, `sba_autopilot.SBAAutopilot.run_once`.
- Produces: `async def agent_loop_tick() -> dict` that (a) processes due handoffs, and (b) for each active mandate with `status=="running"`, dispatches the worker once; otherwise stays idle. The old `_run_due_tasks_safe` self-scheduling of SEO/Website/Ads/Analytics is removed — those now run only via CEO mandates.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_ceo_loop.py
import asyncio
from admin.agency import agent_loop as al
from admin.agency import mandates as m


def test_loop_runs_only_active_mandates():
    async def run():
        await m.init_mandates_table()
        await m.set_mandate("dummy", "running", "loop", {"kind": "agency", "workspace_id": "ws_agency"})
        # patch run_worker to count calls
        calls = []
        import admin.agency.workers as w
        orig = w.run_worker
        async def spy(worker, task, ctx):
            calls.append(worker)
            return {"ok": True}
        w.run_worker = spy
        res = await al.agent_loop_tick()
        w.run_worker = orig
        assert "dummy" in calls, f"expected mandate worker to run, got {calls}"
    asyncio.run(run())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:\Users\TAUSHEF\Downloads\int && python -m pytest tests/test_ceo_loop.py -v`
Expected: FAIL — assertion or `ModuleNotFoundError` until loop is re-homed.

- [ ] **Step 3: Write minimal implementation** (replace `_tick_once` / `agent_loop_tick` in `agent_loop.py`, keep `_auto_process_due_handoffs`)

```python
async def _tick_once() -> dict[str, Any]:
    """CEO-mandate-driven tick: never self-schedules. Runs only active mandates."""
    from admin.agency import mandates as mandates_mod
    from admin.agency import workers as workers_mod

    handoffs = await _auto_process_due_handoffs()
    ran: list[str] = []
    for md in await mandates_mod.list_mandates():
        if md.get("status") != "running":
            continue
        worker = md["worker"]
        scope = md.get("scope") or {"kind": "agency", "workspace_id": "agency"}
        try:
            await workers_mod.run_worker(worker, md.get("standing_task", ""), {"scope": scope})
            ran.append(worker)
        except Exception as exc:  # noqa: BLE001
            logger.exception("agent-loop: worker %s failed: %s", worker, exc)
    return {"mandates_ran": ran, "handoffs": handoffs, "at": time.time()}


async def agent_loop_tick() -> dict[str, Any]:
    try:
        return await asyncio.wait_for(_tick_once(), timeout=AGENT_LOOP_TICK_TIMEOUT_SECONDS)
    except asyncio.TimeoutError:
        logger.warning("agent-loop: tick exceeded %ss", AGENT_LOOP_TICK_TIMEOUT_SECONDS)
        return {"error": "tick_timeout"}
    except Exception as exc:  # noqa: BLE001
        logger.exception("agent-loop: tick crashed: %s", exc)
        return {"error": str(exc)}
```

Also remove the now-unused `_run_due_tasks_safe` and its `run_due_tasks` import (keep `_auto_process_due_handoffs`). The `agent_loop_forever()` stays the same driver.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd C:\Users\TAUSHEF\Downloads\int && python -m pytest tests/test_ceo_loop.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add admin/agency/agent_loop.py tests/test_ceo_loop.py
git commit -q -m "refactor: agent loop now runs only CEO-active mandates"
```

---

### Task 7: CEO chat + floor state + WebSocket endpoints

**Files:**
- Modify: `admin/api/routes/ceo.py` (add `/state`, `/delegate`, `/ws/office`)
- Create: `tests/test_ceo_api.py`

**Interfaces:**
- Consumes: `admin.agency.ceo_controller.ceo_controller`, `admin.agency.memory`, `get_floor_activity`, `append_agent_activity_log`.
- Produces:
  - `GET /api/ceo/state` → `ceo_controller.get_state()` (CEO + workers + mandates + floor).
  - `POST /api/ceo/delegate` → body `{worker, task, scope, standing?}` → `ceo_controller.delegate(...)`.
  - `WebSocket /ws/office` → on connect streams current `get_state()` then pushes `agent_activity_log` / mandate changes. Keep simple: broadcast floor activity every few seconds via `get_floor_activity` + memory reflections.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_ceo_api.py
from fastapi.testclient import TestClient
from admin.main import app


def test_ceo_state_endpoint():
    client = TestClient(app)
    res = client.get("/api/ceo/state")
    assert res.status_code == 200
    body = res.json()
    assert "workers" in body and "mandates" in body and "floor" in body
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:\Users\TAUSHEF\Downloads\int && python -m pytest tests/test_ceo_api.py -v`
Expected: FAIL — 404 for `/api/ceo/state`.

- [ ] **Step 3: Write minimal implementation** (append to `admin/api/routes/ceo.py`)

```python
from fastapi import WebSocket, WebSocketDisconnect
from admin.agency.ceo_controller import ceo_controller as ctrl


class DelegateRequest(BaseModel):
    worker: str
    task: str
    scope: dict = {"kind": "agency", "workspace_id": "agency"}
    standing: bool = False


@router.get("/state")
async def ceo_state():
    return await ctrl.get_state()


@router.post("/delegate")
async def ceo_delegate(body: DelegateRequest):
    return await ctrl.delegate(body.worker, body.task, body.scope, standing=body.standing)


@router.websocket("/ws/office")
async def ws_office(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            from admin.workspace.manager import get_floor_activity
            state = await ctrl.get_state()
            await ws.send_json(state)
            await asyncio.sleep(3)
    except WebSocketDisconnect:
        return
```

Add `import asyncio` at top of `admin/api/routes/ceo.py` if not present.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd C:\Users\TAUSHEF\Downloads\int && python -m pytest tests/test_ceo_api.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add admin/api/routes/ceo.py tests/test_ceo_api.py
git commit -q -m "feat: CEO state, delegate, and office websocket endpoints"
```

---

### Task 8: Gate direct worker chat behind CEO

**Files:**
- Modify: `admin/api/routes/agent_aliases.py` — any `/api/agents/{id}/chat` route
- Create: `tests/test_gate.py`

**Interfaces:**
- Consumes: existing alias routes; `ceo_controller` for redirect message.
- Produces: direct boss→worker chat returns `402/redirect` instructing "Talk to the CEO at /api/ceo/chat". Worker tasks are only reachable through CEO `delegate`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_gate.py
from fastapi.testclient import TestClient
from admin.main import app


def test_direct_worker_chat_is_gated():
    client = TestClient(app)
    res = client.post("/api/agents/sba/chat", json={"message": "do outreach"})
    assert res.status_code in (400, 403, 426)
    body = res.json()
    assert "CEO" in body.get("detail", "") or "ceo" in str(body).lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:\Users\TAUSHEF\Downloads\int && python -m pytest tests/test_gate.py -v`
Expected: FAIL — current endpoint returns 200 (ungated).

- [ ] **Step 3: Write minimal implementation**

In `admin/api/routes/agent_aliases.py`, locate the worker chat handler (function handling `/api/agents/{id}/chat` / `agent_chat`). Wrap it so it rejects direct boss chat:

```python
@app_aliases.post("/agents/{agent_id}/chat")
async def agent_chat(agent_id: str, body: ChatRequest):
    # CEO-gated: boss may only talk to the CEO, not workers directly.
    return JSONResponse(
        status_code=426,
        content={"error": "direct_worker_chat_disabled",
                 "detail": "Boss can only talk to the CEO. Use POST /api/ceo/chat and let the CEO delegate to "
                           + agent_id + "."},
    )
```

(If a different web framework decorator is used in that file, mirror its pattern — the key behavior is: reject direct worker chat with a clear pointer to `/api/ceo/chat`.)

- [ ] **Step 4: Run test to verify it passes**

Run: `cd C:\Users\TAUSHEF\Downloads\int && python -m pytest tests/test_gate.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add admin/api/routes/agent_aliases.py tests/test_gate.py
git commit -q -m "feat: gate direct worker chat behind CEO"
```

---

### Task 9: CEO reflection digest to boss

**Files:**
- Modify: `admin/agency/ceo_controller.py` (add `async def digest(self) -> str`)
- Modify: `admin/api/routes/ceo.py` (add `GET /api/ceo/digest`)
- Create: `tests/test_digest.py`

**Interfaces:**
- Consumes: `admin.agency.memory.get_memory` for each active worker + CEO; `mandates.list_mandates`.
- Produces: a short plaintext digest: what's running, what's stuck (error/empty memory), and recommended fixes. Returns string.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_digest.py
import asyncio
from admin.agency import ceo_controller as c
from admin.agency import memory as mem


def test_digest_mentions_running_mandate():
    async def run():
        await mem.init_memory_tables()
        await mem.record_event("sba", "task", "emailed lead", {"kind": "agency"})
        await c.ceo_controller.register()
        # ensure a mandate exists
        from admin.agency import mandates as m
        await m.init_mandates_table()
        await m.set_mandate("sba", "running", "lead loop", {"kind": "agency", "workspace_id": "agency"})
        d = await c.ceo_controller.digest()
        assert "sba" in d.lower() and "running" in d.lower()
    asyncio.run(run())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:\Users\TAUSHEF\Downloads\int && python -m pytest tests/test_digest.py -v`
Expected: FAIL — `AttributeError: 'CEOController' object has no attribute 'digest'`

- [ ] **Step 3: Write minimal implementation** (add to `CEOController`)

```python
    async def digest(self) -> str:
        from admin.agency import mandates as mandates_mod
        lines = ["CEO Digest:"]
        for md in await mandates_mod.list_mandates():
            mem = await mem_mod.get_memory(md["worker"])
            last = mem["stream"][0]["text"] if mem["stream"] else "(no activity)"
            lines.append(f"- {md['worker']}: {md['status']} | last: {last[:80]}")
        if len(lines) == 1:
            lines.append("- no active mandates")
        return "\n".join(lines)
```

Add `import admin.agency.memory as mem_mod` at top of `ceo_controller.py`.

- [ ] **Step 4: Add API route** in `admin/api/routes/ceo.py`

```python
@router.get("/digest")
async def ceo_digest():
    return {"digest": await ctrl.digest()}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd C:\Users\TAUSHEF\Downloads\int && python -m pytest tests/test_digest.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add admin/agency/ceo_controller.py admin/api/routes/ceo.py tests/test_digest.py
git commit -q -m "feat: CEO periodic digest from memory + mandates"
```

---

### Task 10: Frontend — remove Paperclip design

**Files:**
- Delete: `agency-frontend/src/app/paperclip.css`
- Modify: `agency-frontend/src/app/globals.css` (remove Paperclip token block; add "Agency Office" tokens)
- Modify/rewrite: `agency-frontend/src/app/admin/components/BreadcrumbBar.js`, `agency-frontend/src/app/admin/dashboard/org/page.jsx`, `agency-frontend/src/app/admin/dashboard/page.js`, `agency-frontend/src/app/admin/dashboard/tickets/page.jsx`, `agency-frontend/src/components/ActivityCharts.jsx` — replace `Paperclip exact` references with neutral "Agency Office" components.
- Create: `agency-frontend/src/app/admin/office/page.jsx` (placeholder that we fill in Task 11)
- Create: `tests/frontend/test_no_paperclip.py` (or a grep-based check script)

**Interfaces:**
- Consumes: nothing (cleanup).
- Produces: no remaining `github.com/paperclipai` references; `globals.css` defines `--office-*` tokens; build still passes.

- [ ] **Step 1: Write the failing check**

```python
# tests/frontend/test_no_paperclip.py
import subprocess, sys, os
root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "agency-frontend"))
out = subprocess.run(["findstr", "/si", "paperclipai", "paperclip.css"], cwd=root,
                     capture_output=True, text=True, shell=True)
assert out.stdout.strip() == "", f"paperclip references remain:\n{out.stdout}"
```

- [ ] **Step 2: Run check to verify it fails**

Run: `cd C:\Users\TAUSHEF\Downloads\int && python -m pytest tests/frontend/test_no_paperclip.py -v`
Expected: FAIL — paperclip references found.

- [ ] **Step 3: Remove Paperclip**

1. Delete `agency-frontend/src/app/paperclip.css`.
2. In `agency-frontend/src/app/globals.css`, replace the `Paperclip Design System` + `--Paperclip-*` token block with:

```css
/* Agency Office Design System */
:root {
  --office-bg: #0f1115;
  --office-panel: #161a21;
  --office-border: #232a33;
  --office-text: #e6e9ef;
  --office-muted: #8b94a3;
  --office-accent: #6E1423; /* maroon, agency brand */
  --office-gold: #F4D35E;
  --office-ceo: #F4D35E;
  --office-sba: #4ea1ff;
}
```

3. In each flagged component, drop the `/* ... Paperclip exact ... */` comments and any `paperclip.css` import; keep the component but restyle with `--office-*` tokens (no functional change to props).

- [ ] **Step 4: Run check + build to verify**

Run: `cd C:\Users\TAUSHEF\Downloads\int && python -m pytest tests/frontend/test_no_paperclip.py -v`
Expected: PASS
Run: `cd C:\Users\TAUSHEF\Downloads\int\agency-frontend && npm run lint`
Expected: PASS (no errors)

- [ ] **Step 5: Commit**

```bash
git add agency-frontend/src/app/globals.css agency-frontend/src/app/paperclip.css agency-frontend/src/app/admin/components/BreadcrumbBar.js agency-frontend/src/app/admin/dashboard/page.js agency-frontend/src/app/admin/dashboard/org/page.jsx agency-frontend/src/app/admin/dashboard/tickets/page.jsx agency-frontend/src/components/ActivityCharts.jsx tests/frontend/test_no_paperclip.py
git commit -q -m "refactor: remove Paperclip design, add Agency Office tokens"
```

---

### Task 11: Frontend — PixiJS office floor + CEO chat + SBA live panel

**Files:**
- Create: `agency-frontend/src/app/admin/office/page.jsx` (office floor + CEO chat)
- Create: `agency-frontend/src/app/admin/office/OfficeFloor.jsx` (PixiJS floor)
- Create: `agency-frontend/src/app/admin/office/CeoChat.jsx` (boss→CEO drawer)
- Create: `agency-frontend/src/app/admin/office/SbaLivePanel.jsx` (live SBA work)
- Create: `agency-frontend/src/hooks/useOfficeSocket.js` (WebSocket `/ws/office` client)
- Modify: `agency-frontend/package.json` (add `pixi.js` dep)
- Create: `tests/frontend/test_office_entry.py` (build/import smoke check)

**Interfaces:**
- Consumes: `GET /api/ceo/state`, `POST /api/ceo/chat`, `WebSocket /ws/office`, `GET /api/ceo/digest` from backend (Tasks 4, 7, 9). `useOfficeSocket` returns `{state, send, connected}`.
- Produces: an office floor with desks for `sba, seo, website, ads, content, social, analytics` + a central CEO desk; clicking CEO opens `CeoChat`; SBA desk shows `SbaLivePanel` streaming live work from the socket; desks show status (working/idle/error) driven by `state.floor` + mandates.

- [ ] **Step 1: Add pixi.js dep**

Edit `agency-frontend/package.json` `dependencies` to include:
```json
"pixi.js": "^8.6.0"
```
Then run `cd C:\Users\TAUSHEF\Downloads\int\agency-frontend && npm install` and confirm `pixi.js` installed.

- [ ] **Step 2: Write the office socket hook**

```js
// agency-frontend/src/hooks/useOfficeSocket.js
import { useEffect, useRef, useState } from "react";

export function useOfficeSocket() {
  const [state, setState] = useState(null);
  const [connected, setConnected] = useState(false);
  const ws = useRef(null);
  useEffect(() => {
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    const url = `${proto}://${window.location.host}/api/ceo/ws/office`;
    const socket = new WebSocket(url);
    ws.current = socket;
    socket.onopen = () => setConnected(true);
    socket.onclose = () => setConnected(false);
    socket.onmessage = (e) => {
      try { setState(JSON.parse(e.data)); } catch {}
    };
    return () => socket.close();
  }, []);
  return { state, connected };
}
```

- [ ] **Step 3: Write OfficeFloor (PixiJS)**

```jsx
// agency-frontend/src/app/admin/office/OfficeFloor.jsx
import { useEffect, useRef } from "react";
import { Application, Graphics, Text } from "pixi.js";

const DESKS = [
  { id: "ceo", label: "CEO (Michael)", x: 400, y: 300, color: 0xF4D35E },
  { id: "sba", label: "SBA", x: 150, y: 150, color: 0x4ea1ff },
  { id: "seo", label: "SEO", x: 650, y: 150, color: 0x6E1423 },
  { id: "website", label: "Website", x: 150, y: 450, color: 0x6E1423 },
  { id: "ads", label: "Ads", x: 650, y: 450, color: 0x6E1423 },
  { id: "content", label: "Content", x: 250, y: 300, color: 0x232a33 },
  { id: "social", label: "Social", x: 550, y: 300, color: 0x232a33 },
  { id: "analytics", label: "Analytics", x: 400, y: 120, color: 0x232a33 },
];

export default function OfficeFloor({ onSelectCeo, floor }) {
  const ref = useRef(null);
  useEffect(() => {
    let app; let destroyed = false;
    (async () => {
      app = new Application();
      await app.init({ width: 800, height: 600, background: "#0f1115" });
      if (destroyed) { app.destroy(); return; }
      ref.current.appendChild(app.canvas);
      for (const d of DESKS) {
        const g = new Graphics().roundRect(d.x - 50, d.y - 35, 100, 70, 8).fill(d.color);
        const t = new Text({ text: d.label, style: { fill: 0xffffff, fontSize: 12 } });
        t.x = d.x - 40; t.y = d.y - 10;
        if (d.id === "ceo") g.eventMode = "static", g.cursor = "pointer", g.on("pointerdown", onSelectCeo);
        app.stage.addChild(g, t);
      }
    })();
    return () => { destroyed = true; if (app) app.destroy(true); };
  }, [onSelectCeo]);
  return <div ref={ref} />;
}
```

- [ ] **Step 4: Write CeoChat + SbaLivePanel + page**

```jsx
// agency-frontend/src/app/admin/office/CeoChat.jsx
import { useState } from "react";
export default function CeoChat({ onClose }) {
  const [msg, setMsg] = useState("");
  const [reply, setReply] = useState("");
  async function send() {
    const r = await fetch("/api/ceo/chat", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: msg }),
    });
    const j = await r.json();
    setReply(j.response || "");
  }
  return (
    <div style={{ position: "fixed", right: 0, top: 0, width: 360, height: "100%", background: "var(--office-panel)", color: "var(--office-text)", padding: 16 }}>
      <button onClick={onClose}>Close</button>
      <textarea value={msg} onChange={(e) => setMsg(e.target.value)} style={{ width: "100%", height: 80 }} />
      <button onClick={send}>Send to CEO</button>
      <p>{reply}</p>
    </div>
  );
}
```

```jsx
// agency-frontend/src/app/admin/office/SbaLivePanel.jsx
export default function SbaLivePanel({ floor }) {
  const sba = (floor || []).find((a) => a.agent_type === "sba");
  return (
    <div style={{ background: "var(--office-panel)", color: "var(--office-text)", padding: 12 }}>
      <h3>SBA live</h3>
      <p>status: {sba?.status || "idle"}</p>
      <p>{sba?.task || "watching leads"}</p>
    </div>
  );
}
```

```jsx
// agency-frontend/src/app/admin/office/page.jsx
"use client";
import { useState } from "react";
import OfficeFloor from "./OfficeFloor";
import CeoChat from "./CeoChat";
import SbaLivePanel from "./SbaLivePanel";
import { useOfficeSocket } from "../../../hooks/useOfficeSocket";

export default function OfficePage() {
  const [chatOpen, setChatOpen] = useState(false);
  const { state } = useOfficeSocket();
  const floor = state?.floor || [];
  return (
    <div style={{ background: "var(--office-bg)", minHeight: "100vh", color: "var(--office-text)" }}>
      <h1>TAGS Agency — Michael's Office</h1>
      <OfficeFloor onSelectCeo={() => setChatOpen(true)} floor={floor} />
      <SbaLivePanel floor={floor} />
      {chatOpen && <CeoChat onClose={() => setChatOpen(false)} />}
    </div>
  );
}
```

- [ ] **Step 5: Write smoke check + run lint/build**

```python
# tests/frontend/test_office_entry.py
import os, subprocess
root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "agency-frontend"))
assert os.path.exists(os.path.join(root, "src/app/admin/office/page.jsx")), "office page missing"
out = subprocess.run(["npm", "run", "lint"], cwd=root, capture_output=True, text=True)
assert out.returncode == 0, out.stdout + out.stderr
```

Run: `cd C:\Users\TAUSHEF\Downloads\int && python -m pytest tests/frontend/test_office_entry.py -v`
Expected: PASS
Run: `cd C:\Users\TAUSHEF\Downloads\int\agency-frontend && npm run lint`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add agency-frontend/src/app/admin/office agency-frontend/src/hooks/useOfficeSocket.js agency-frontend/package.json tests/frontend/test_office_entry.py
git commit -q -m "feat: PixiJS office floor, CEO chat, SBA live panel"
```

---

### Task 12: Final — backend + frontend test sweep

**Files:**
- None new; run full suites.

- [ ] **Step 1: Run backend tests**

Run: `cd C:\Users\TAUSHEF\Downloads\int && python -m pytest -q`
Expected: all pass (no regressions from `agent_loop`/gate changes).

- [ ] **Step 2: Run frontend lint**

Run: `cd C:\Users\TAUSHEF\Downloads\int\agency-frontend && npm run lint`
Expected: PASS

- [ ] **Step 3: Run frontend build**

Run: `cd C:\Users\TAUSHEF\Downloads\int\agency-frontend && npm run build`
Expected: build succeeds.

- [ ] **Step 4: Commit (no-op if clean) and report**

If everything green, report completion with the acceptance checklist mapped to spec.

---

## Self-Review (against spec)

- **Spec coverage:** Autonomy model (A) → Tasks 2,3,4,6,8. Memory/plan/reflection → Task 5,9. Frontend office floor → Tasks 10,11. WebSocket → Task 7,11. SBA live work → Task 11 (SbaLivePanel). Paperclip removal → Task 10. Agency/client scope → `scope` field threaded through Tasks 1-4,7. Acceptance criteria → Task 12.
- **Placeholder scan:** No TBD/TODO. Every code step shows full code or an exact file to edit. `_run_passthrough` is intentional (specialist live-exec wiring deferred to a clearly-scoped follow-up, documented in code comment, not a placeholder).
- **Type consistency:** `run_worker(worker, task, ctx)` used identically in Tasks 2,3,4,6. `get_state()` returns `{ceo, workers, mandates, floor}` in Tasks 4,7,11. `mandates.set_mandate/get_mandate/list_mandates/clear_mandate` consistent across Tasks 1,4,6,9. `memory.get_memory/record_event/set_plan/add_reflection` consistent Tasks 5,9.
- **One gap closed:** SBA `run_once` is referenced (exists in `sba_autopilot.py`); `register_builtins` calls it in Task 3.
- **One risk noted:** `agent_aliases.py` exact decorator/framework differs; Task 8 instructs mirroring the existing pattern (only behavior matters: reject direct worker chat → point to `/api/ceo/chat`).
