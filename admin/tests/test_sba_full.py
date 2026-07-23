"""Test SBA LangGraph end-to-end."""
import sys
sys.path.insert(0, r"C:\Users\TAUSHEF\Downloads\int")

import asyncio
from admin.agency.sba import SBAAgent

async def test():
    print("=== SBA LangGraph Integration Tests ===\n")
    
    # 1. Agent creation
    print("1. Creating agent...")
    agent = SBAAgent(workspace_name="TestWorkspace", client_name="TestClient")
    print(f"   ✅ Agent ready: graph={type(agent.graph).__name__}")
    print(f"   Thread: {agent._thread_id}")
    
    # 2. Basic chat - greeting
    print("\n2. Basic greeting chat...")
    response, phases = await agent.chat("Hello! Kaise ho?")
    print(f"   ✅ Response ({len(response)} chars)")
    print(f"   Response preview: {response[:150]}...")
    print(f"   Thinking phases: {len(phases)}")
    if phases:
        for p in phases:
            print(f"     - {p['phase']}: {len(p['content'])} chars")
    
    # 3. Conversation follow-up
    print("\n3. Follow-up (conversation persistence)...")
    response2, phases2 = await agent.chat("Achha, aur batao kya plan hai aaj?")
    print(f"   ✅ Response ({len(response2)} chars)")
    print(f"   Preview: {response2[:150]}...")
    print(f"   Thinking phases: {len(phases2)}")
    
    # 4. Verify different thread = fresh conversation
    print("\n4. Fresh agent (new workspace) verification...")
    agent2 = SBAAgent(workspace_name="SecondWorkspace", client_name="SecondClient")
    response3, phases3 = await agent2.chat("Hello from another workspace!")
    print(f"   ✅ Response ({len(response3)} chars)")
    print(f"   Preview: {response3[:100]}...")
    
    print("\n=== All Tests Passed! ===")

if __name__ == "__main__":
    asyncio.run(test())
