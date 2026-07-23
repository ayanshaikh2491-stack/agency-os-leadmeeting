"""Test LangGraph SBA graph compilation."""
import sys
sys.path.insert(0, r"C:\Users\TAUSHEF\Downloads\int")

from admin.agency.langgraph_sba import build_sba_graph
from langgraph.graph.state import CompiledStateGraph

print("Building SBA LangGraph...")
graph = build_sba_graph()
print(f"Graph type: {type(graph).__name__}")
assert isinstance(graph, CompiledStateGraph), "Graph should be compiled"
print("✅ Graph compiled successfully!")

# Check nodes
print(f"Nodes: {list(graph.nodes.keys())}")
print(f"Edges: {list(graph.edges.keys()) if hasattr(graph, 'edges') else 'N/A'}")
print("\n✅ All checks passed!")
