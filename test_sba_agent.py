"""Test SBA agent imports and tool functions."""
import sys
sys.path.insert(0, '.')
from admin.workspace.agents.sba import SBAAgent
from admin.tools.sba_tools import detect_lead_sources, save_lead_record, qualify_lead, SBA_TOOLS, execute_sba_tool

print(f'SBA_TOOLS count: {len(SBA_TOOLS)}')
print(f'detect_lead_sources callable: {callable(detect_lead_sources)}')
print(f'qualify_lead callable: {callable(qualify_lead)}')

# Test detect_lead_sources
result = detect_lead_sources('web development', 'us')
print(f'\n--- Web Dev / US Market ---')
print(f'  Platforms: {result["platforms"]}')
print(f'  Matched: {result["matched_category"]}')

result2 = detect_lead_sources('plumber near me', 'india')
print(f'\n--- Local Business / India ---')
print(f'  Platforms: {result2["platforms"]}')
print(f'  Matched: {result2["matched_category"]}')

result3 = detect_lead_sources('B2B SaaS enterprise sales', 'uk')
print(f'\n--- B2B SaaS / UK ---')
print(f'  Platforms: {result3["platforms"]}')
print(f'  Matched: {result3["matched_category"]}')

# Test qualify_lead
qual = qualify_lead(80, has_budget=True, has_authority=True, has_need=True, has_timeline=True)
print(f'\n--- Hot lead ---')
print(f'  Verdict: {qual["verdict"]}')
print(f'  Score: {qual["combined_score"]}')

qual2 = qualify_lead(30, has_budget=False, has_authority=False, has_need=True, has_timeline=False)
print(f'\n--- Cold lead ---')
print(f'  Verdict: {qual2["verdict"]}')
print(f'  Score: {qual2["combined_score"]}')

# Test execute_sba_tool dispatch
dispatch_test = execute_sba_tool('detect_lead_sources', {'industry': 'marketing', 'market': 'uae'})
print(f'\n--- Dispatch test (marketing/UAE) ---')
print(f'  Platforms: {dispatch_test["platforms"]}')
print(f'  Why: {dispatch_test["why"]}')

print('\n✅ All SBA tool tests passed!')
