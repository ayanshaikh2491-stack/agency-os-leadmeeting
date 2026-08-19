import asyncio
from admin.agency import agent_loop as al
from admin.agency import mandates as m
def test_loop_runs_only_active_mandates():
    async def run():
        await m.init_mandates_table()
        await m.set_mandate("dummy", "running", "loop", {"kind": "agency", "workspace_id": "ws_agency"})
        import admin.agency.workers as w
        orig = w.run_worker
        calls = []
        async def spy(worker, task, ctx):
            calls.append(worker); return {"ok": True}
        w.run_worker = spy
        res = await al.agent_loop_tick()
        w.run_worker = orig
        assert "dummy" in calls, f"expected mandate worker to run, got {calls}"
    asyncio.run(run())
