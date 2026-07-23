"""Debug LangGraph SBA execution step by step."""
import sys
sys.path.insert(0, r"C:\Users\TAUSHEF\Downloads\int")

import asyncio
import logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

from admin.agency.langgraph_sba import build_sba_graph

async def debug():
    graph = build_sba_graph()
    
    # Initial state
    state = {
        "messages": [{"role": "user", "content": "Hello! Kaise ho?"}],
        "workspace_name": "DebugWorkspace",
        "client_name": "DebugClient",
        "browser_name": "sba",
        "stealth_mode": True,
        "conversation_history": [],
        "thinking_phases": [],
        "tool_round": 0,
        "final_output": "",
        "error": None,
    }
    
    # Stream the events
    print("\n=== Streaming graph execution ===\n")
    async for event in graph.astream(state, config={"configurable": {"thread_id": "debug_1"}}):
        for node_name, data in event.items():
            if node_name == "__end__":
                continue
            print(f"\n--- Node: {node_name} ---")
            if isinstance(data, dict):
                # Show keys but not full messages
                for k, v in data.items():
                    if k == "messages":
                        for m in v:
                            role = m.get("role", "?")
                            content = m.get("content", "")
                            tool_calls = m.get("tool_calls", [])
                            if role == "tool":
                                print(f"  tool result: {content[:100]}...")
                            elif tool_calls:
                                print(f"  assistant with {len(tool_calls)} tool calls")
                            else:
                                print(f"  {role}: {content[:150]}...")
                    elif k == "thinking_phases":
                        print(f"  phases: [{', '.join(p['phase'] for p in v)}]")
                    elif k == "final_output":
                        print(f"  final_output: {v[:150]}...")
                    elif k == "error":
                        print(f"  error: {v}")
                    elif v:
                        print(f"  {k}: {v}")
    
    print("\n=== Done ===")

if __name__ == "__main__":
    asyncio.run(debug())
