"""Test SBA LangGraph end-to-end."""
import sys
sys.path.insert(0, r"C:\Users\TAUSHEF\Downloads\int")

import asyncio
from admin.agency.sba import SBAAgent
from admin.agency.langgraph_sba import build_sba_graph, call_llm, run_tools, finalize

async def test():
    # 1. Test graph compilation (already done, but verify via SBAAgent)
    print("1. Testing SBAAgent initialization...")
    agent = SBAAgent(workspace_name="TestWorkspace", client_name="TestClient")
    print(f"   ✅ Agent created: graph={type(agent.graph).__name__}")
    
    # 2. Check graph structure
    print("\n2. Graph structure:")
    for node_name in agent.graph.nodes:
        print(f"   - Node: {node_name}")
    
    # 3. Test state schema
    print("\n3. Testing state schema...")
    from admin.agency.langgraph_sba import SBAGraphState
    print(f"   ✅ State schema available: {SBAGraphState.__name__}")
    
    # 4. Test chat (will use OpenAI - so check if it works)
    print("\n4. Testing chat method (requires LLM)...")
    try:
        response, phases = await agent.chat(
            "Hello! Kaise ho?",
            conversation_history=[],
        )
        print(f"   ✅ Response received ({len(response)} chars)")
        if phases:
            print(f"   - Thinking phases: {len(phases)}")
            for p in phases:
                print(f"     * {p['phase']}: {len(p['content'])} chars")
        else:
            print(f"   - No thinking phases (LLM may not have output think blocks)")
        print(f"   - First 100 chars: {response[:100]}")
    except Exception as e:
        print(f"   ❌ Chat failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ All tests complete!")

if __name__ == "__main__":
    asyncio.run(test())
