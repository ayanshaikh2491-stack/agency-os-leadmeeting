import asyncio
import time
from admin.agency import memory as mem

def test_memory_roundtrip():
    # Unique agent id so the test is isolated from data persisted in the shared
    # SQLite DB by previous runs (the DB is not wiped between test invocations).
    agent = f"test_sba_{int(time.time() * 1000)}"
    async def run():
        await mem.init_memory_tables()
        await mem.record_event(agent, "task", "emailed Al's Auto", {"kind": "agency"})
        await mem.set_plan(agent, ["run lead loop", "book meetings"])
        await mem.add_reflection(agent, "email cap reached; slow down")
        m = await mem.get_memory(agent)
        assert any("Al's Auto" in e["text"] for e in m["stream"])
        assert "book meetings" in m["plan"]
        assert len(m["reflections"]) == 1
    asyncio.run(run())
