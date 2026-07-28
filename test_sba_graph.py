"""Test SBAAgent graph compilation and structure."""
import sys
sys.path.insert(0, '.')

from admin.workspace.agents.sba import (
    build_sba_workspace_graph,
    SBAAgent,
    SBA_ALL_TOOLS,
    _extract_sba_phases,
    _strip_think_blocks,
    MAX_TOOL_ROUNDS,
)

# Test 1: Graph builds without error
graph = build_sba_workspace_graph()
print(f'Graph compiled successfully')
print(f'  Nodes: {list(graph.nodes.keys())}')

# Test 2: SBAAgent creates without error
agent = SBAAgent(workspace_name="test", client_name="Test Client")
print(f'SBAAgent created for workspace: test')
print(f'  Thread: {agent._thread_id}')
print(f'  Chrome registered: {agent._chrome is not None}')

# Test 3: Tool counts
chrome_count = sum(1 for t in SBA_ALL_TOOLS if t.get('function', {}).get('name', '').startswith('chrome_'))
sba_count = sum(1 for t in SBA_ALL_TOOLS if t.get('function', {}).get('name', '') in
    ('detect_lead_sources', 'save_lead_record', 'list_saved_leads', 'qualify_lead'))
print(f'Tool counts:')
print(f'  Chrome tools: {chrome_count}')
print(f'  SBA tools: {sba_count}')
print(f'  Total: {len(SBA_ALL_TOOLS)}')
print(f'  MAX_TOOL_ROUNDS: {MAX_TOOL_ROUNDS}')

# Test 4: Thinking phase extraction
test_content = """```think
### 1. Deconstruct
Client is a B2B SaaS company targeting UK market.

### 2. Seek
Should use LinkedIn and Crunchbase.
```
Some visible text here.
"""
phases = _extract_sba_phases(test_content)
print(f'Phase extraction: {len(phases)} phases')
for p in phases:
    print(f'  Phase: {p["phase"]} ({len(p["content"])} chars)')

# Test 5: Think block stripping
stripped = _strip_think_blocks(test_content)
print(f'Stripped content: "{stripped.strip()}"')

print('\nAll SBA agent compilation tests passed!')
