"""Lightning test: SBA agent direct chat with LLM + Chrome.

Usage: python admin/tests/live/live_sba_direct.py ["optional prompt"]
"""
import sys, asyncio, logging
sys.path.insert(0, '.')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('test')

DEFAULT_PROMPT = (
    "Mera client B2B SaaS hai jo US enterprise market mein workflow automation "
    "bechta hai. Target audience CTOs aur Heads of Engineering hain. "
    "Kahan se leads find karu? Chrome use karke dekho."
)

async def main():
    from admin.workspace.agents.sba import SBAAgent

    prompt = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PROMPT

    agent = SBAAgent(workspace_name="TestClient", client_name="Test Client")
    print("SBA Agent created, starting chat...")

    # Direct chat — no workspace manager
    print("Calling LLM... (OpenCode Zen API, might take 10-60s)")
    sys.stdout.flush()
    response, phases = await agent.chat(prompt)

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
