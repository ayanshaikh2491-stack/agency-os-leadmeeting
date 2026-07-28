"""Final comprehensive SBA agent verification."""
import sys, inspect, importlib
sys.path.insert(0, '.')

print("=" * 50)
print("SBA AGENT E2E VERIFICATION")
print("=" * 50)

# 1. New SBAAgent module path
from admin.workspace.agents.sba import SBAAgent as NewSBA
assert 'workspace.agents.sba' in NewSBA.__module__
print(f'[1/7] New SBAAgent module: {NewSBA.__module__}')

# 2. Agent creation + Chrome per workspace
agent = NewSBA(workspace_name="E2E-Test", client_name="E2E Client")
assert agent._chrome is not None
nodes = list(agent.graph.nodes.keys())
assert 'call_llm' in nodes and 'run_tools' in nodes and 'finalize' in nodes
print(f'[2/7] SBAAgent created, Chrome registered, nodes: {nodes}')

# 3. Manager routes to new agent
src = inspect.getsource(importlib.import_module('admin.workspace.manager').route_to_agent)
assert 'admin.workspace.agents.sba' in src
print(f'[3/7] route_to_agent -> workspace.agents.sba')

# 4. All 19 tools (15 Chrome + 4 SBA)
from admin.tools.sba_tools import SBA_TOOLS, execute_sba_tool
from admin.tools.chrome_tool import CHROME_TOOLS
total = len(CHROME_TOOLS) + len(SBA_TOOLS)
assert len(CHROME_TOOLS) == 15, f'Expected 15 Chrome tools, got {len(CHROME_TOOLS)}'
assert len(SBA_TOOLS) == 4, f'Expected 4 SBA tools, got {len(SBA_TOOLS)}'
assert total == 19
print(f'[4/7] Tools: {len(CHROME_TOOLS)} Chrome + {len(SBA_TOOLS)} SBA = {total}')

# 5. Lead detection for all 10 categories
tests = [
    ('B2B SaaS enterprise', 'b2b_saas'),
    ('web development with React', 'tech_web'),
    ('mobile app Flutter developer', 'tech_mobile'),
    ('digital marketing agency', 'marketing'),
    ('business consultant coach', 'consulting'),
    ('UI UX graphic design', 'design'),
    ('content writer copywriter', 'writing'),
    ('video editor animator', 'video_photo'),
    ('Shopify ecommerce store', 'ecommerce'),
    ('local plumber electrician', 'local_business'),
    ('python developer API', 'software'),
    ('something generic random', 'general'),
]
for industry, expected in tests:
    r = execute_sba_tool('detect_lead_sources', {'industry': industry, 'market': 'global'})
    assert r['matched_category'] == expected, f'"{industry}" -> expected {expected}, got {r["matched_category"]}'
print(f'[5/7] Lead detection: all {len(tests)} categories match')

# 6. BANT qualification
q_hot = execute_sba_tool('qualify_lead', {'lead_score': 85, 'has_budget': True, 'has_authority': True, 'has_need': True, 'has_timeline': True})
assert q_hot['verdict'] == 'hot'
q_cold = execute_sba_tool('qualify_lead', {'lead_score': 20, 'has_budget': False, 'has_authority': False, 'has_need': False, 'has_timeline': False})
assert q_cold['verdict'] == 'cold'
print(f'[6/7] BANT: hot={q_hot["combined_score"]} cold={q_cold["combined_score"]}')

# 7. Market-specific adjustments
r_us = execute_sba_tool('detect_lead_sources', {'industry': 'web dev', 'market': 'us'})
r_india = execute_sba_tool('detect_lead_sources', {'industry': 'web dev', 'market': 'india'})
assert 'freelancer' in r_india['platforms'], 'India should include Freelancer'
print(f'[7/7] Market adjustments: US={r_us["platforms"][:2]}... India={r_india["platforms"][:3]}...')

print()
print(" ALL 7/7 SBA E2E CHECKS PASSED!")
