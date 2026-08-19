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
