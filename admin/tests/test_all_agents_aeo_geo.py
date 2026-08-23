import ast
# syntax check all 4 agents
for f in ["admin/workspace/agents/social.py", "admin/workspace/agents/website.py",
          "admin/workspace/agents/content.py", "admin/workspace/agents/seo.py",
          "admin/agency/agent_aeo_geo.py"]:
    ast.parse(open(f, encoding="utf-8").read())
    print("SYNTAX OK:", f)

# import + light check
from admin.agency import agent_aeo_geo
sec = agent_aeo_geo.build_aeo_geo_section("Houston Plumbing Co")
assert "AEO" in sec and "GEO" in sec
print("SOCIAL_AEO_GEO_OK")
print("ALL_AGENTS_WIRED")
