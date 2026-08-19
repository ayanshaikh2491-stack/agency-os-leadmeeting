import asyncio
from admin.agency import ceo_controller as c
from admin.agency import memory as mem
from admin.agency import mandates as m
def test_digest_mentions_running_mandate():
    async def run():
        await mem.init_memory_tables()
        await mem.record_event("sba", "task", "emailed lead", {"kind": "agency"})
        await m.init_mandates_table()
        await m.set_mandate("sba", "running", "lead loop", {"kind": "agency", "workspace_id": "agency"})
        c.ceo_controller.register()
        d = await c.ceo_controller.digest()
        assert "sba" in d.lower() and "running" in d.lower()
    asyncio.run(run())
