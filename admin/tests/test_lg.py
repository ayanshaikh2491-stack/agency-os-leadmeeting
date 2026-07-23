"""Test LangGraph availability."""
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing import TypedDict, Annotated
print("LangGraph imports OK")
print("StateGraph:", StateGraph)
print("add_messages:", add_messages)
