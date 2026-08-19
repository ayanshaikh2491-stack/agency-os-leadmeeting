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


ceo_controller = CEOController()
