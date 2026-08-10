"""End-to-end test: run a tiny StateGraph with SupabaseSaver on EC2.

Verifies:
  1. SupabaseSaver(workspace, agent) constructs without ImportError
  2. A 2-node graph runs with the saver (put / put_writes / get_tuple)
  3. Re-running on the same thread resumes from the stored checkpoint
  4. Memory save/get works through the gateway
"""
import asyncio
import os
import sys

sys.path.insert(0, "/home/ubuntu/sba-backend")

from typing import Any, TypedDict

from langgraph.graph import StateGraph, START, END


class State(TypedDict, total=False):
    count: int
    trail: list[str]


def node_a(state: State) -> dict[str, Any]:
    trail = list(state.get("trail") or []) + ["A"]
    return {"trail": trail, "count": (state.get("count") or 0) + 1}


def node_b(state: State) -> dict[str, Any]:
    trail = list(state.get("trail") or []) + ["B"]
    return {"trail": trail}


async def main() -> None:
    from admin.agency.agent_persistence import SupabaseSaver, save_memory, get_memory

    ws = "ws_agency"
    agent = "sba"

    print("== construct saver ==")
    saver = SupabaseSaver(ws, agent)
    print("available:", saver.available)

    print("== build graph ==")
    g = StateGraph(State)
    g.add_node("a", node_a)
    g.add_node("b", node_b)
    g.add_edge(START, "a")
    g.add_edge("a", "b")
    g.add_edge("b", END)
    app = g.compile(checkpointer=saver)

    thread = "test-thread-1"
    print("== run 1 ==")
    r1 = await app.ainvoke({"trail": []}, {"configurable": {"thread_id": thread}})
    print("run1 result:", r1)

    print("== run 2 (same thread, should resume) ==")
    r2 = await app.ainvoke({"trail": []}, {"configurable": {"thread_id": thread}})
    print("run2 result:", r2)

    print("== get_state ==")
    st = await app.aget_state({"configurable": {"thread_id": thread}})
    print("state:", st.values)

    print("== memory save/get ==")
    sv = save_memory(ws, agent, "test_key", {"hello": "world", "n": 1})
    print("save_memory:", sv is not None, sv if sv else "")
    got = get_memory(ws, agent, "test_key")
    print("get_memory:", got)

    ok = r1.get("trail") == ["A", "B"] and r2.get("count", 0) == 2 and got is not None
    print("RESULT:", "PASS" if ok else "FAIL")


if __name__ == "__main__":
    asyncio.run(main())
