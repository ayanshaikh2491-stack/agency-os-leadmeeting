import asyncio
from admin.agency import mandates as m

def test_set_get_clear_mandate():
    async def run():
        await m.init_mandates_table()
        await m.set_mandate(worker="sba", status="running", standing_task="lead->email->meeting loop",
                            scope={"kind": "agency", "workspace_id": "ws_agency"})
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
