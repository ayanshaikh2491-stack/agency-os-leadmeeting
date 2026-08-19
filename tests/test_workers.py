import asyncio
from admin.agency import workers as w


async def _fake_run(task: str, ctx: dict) -> dict:
    return {"ok": True, "echo": task}


def test_run_worker_records_activity():
    async def run():
        w.register_worker("dummy", "Dummy", "test", _fake_run)
        res = await w.run_worker(
            "dummy", "do thing", {"scope": {"kind": "agency", "workspace_id": "ws_agency"}}
        )
        assert res["ok"] is True
        from admin.workspace.manager import get_agent_activity_log

        log = get_agent_activity_log("ws_agency", "dummy")
        assert any("do thing" in e["text"] for e in log)

    asyncio.run(run())


def test_register_builtins_populates_registry():
    from admin.agency import workers as w
    w.register_builtins()
    types = {m["type"] for m in w.list_workers()}
    assert {"sba","seo","website","ads","content","social","analytics"} <= types
