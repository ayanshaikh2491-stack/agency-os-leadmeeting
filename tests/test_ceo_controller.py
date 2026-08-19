import asyncio

from admin.agency import ceo_controller as c


def test_ceo_controller_state_shape():
    async def run():
        c.ceo_controller.register()
        st = await c.ceo_controller.get_state()
        assert "ceo" in st and "workers" in st and "mandates" in st

    asyncio.run(run())
