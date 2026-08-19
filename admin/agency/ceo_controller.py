"""CEO Controller — single brain. Owns the CEO graph, mandates, delegation."""
from __future__ import annotations

from typing import Any

from admin.agency import workers as workers_mod
from admin.agency import mandates as mandates_mod
from admin.agency import memory as mem_mod
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
        scope_kind = "client" if "client" in message.lower() else "agency"
        return {
            "response": response,
            "conversation_id": conv_id,
            "phases": phases,
            "scope_detected": {
                "kind": scope_kind,
                "workspace_id": "agency" if scope_kind == "agency" else "detect",
            },
        }

    async def delegate(self, worker: str, task: str, scope: dict[str, Any], standing: bool = False) -> dict[str, Any]:
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

    async def digest(self) -> str:
        lines = ["CEO Digest:"]
        for md in await mandates_mod.list_mandates():
            mem = await mem_mod.get_memory(md["worker"])
            last = mem["stream"][0]["text"] if mem["stream"] else "(no activity)"
            lines.append(f"- {md['worker']}: {md['status']} | last: {last[:80]}")
        if len(lines) == 1:
            lines.append("- no active mandates")
        return "\n".join(lines)


ceo_controller = CEOController()
