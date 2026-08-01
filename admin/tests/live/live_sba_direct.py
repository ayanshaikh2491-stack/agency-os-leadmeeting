"""Lightning test: SBA agent direct chat with LLM + Chrome."""
import sys, asyncio, logging
sys.path.insert(0, '.')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('test')

async def main():
    from admin.workspace.agents.sba import SBAAgent

    agent = SBAAgent(workspace_name="TestClient", client_name="Test Client")
    print("SBA Agent created, starting chat...")

    # Direct chat — no workspace manager
    print("Calling LLM... (Groq API, might take 10-30s)")
    sys.stdout.flush()
    response, phases = await agent.chat(
        "Mera client B2B SaaS hai jo US enterprise market mein workflow automation "
        "bechta hai. Target audience CTOs aur Heads of Engineering hain. "
        "Kahan se leads find karu? Chrome use karke dekho."
    )

    print("\n" + "="*60)
    print("SBA AGENT RESPONSE:")
    print("="*60)
    print(response[:2000])

    if phases:
        print("\n" + "="*60)
        print("THINKING PHASES:")
        print("="*60)
        for p in phases:
            print(f"\n--- {p['phase'].upper()} ---")
            print(p['content'][:300])

asyncio.run(main())
