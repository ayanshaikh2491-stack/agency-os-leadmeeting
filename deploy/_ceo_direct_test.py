import asyncio
import sys
sys.path.insert(0, "/home/ubuntu/sba-backend")

async def main():
    from admin.agency.ceo import AgencyCEO
    ceo = AgencyCEO()
    print("graph type:", type(ceo.graph).__name__)
    print("checkpointer:", type(ceo.graph.checkpointer).__name__)
    try:
        resp, cid, phases = await ceo.chat("Bhai, 1 line mein status batao", conversation_id="deploy-test-1")
        print("RESP:", resp[:200])
        print("CID:", cid)
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(main())
