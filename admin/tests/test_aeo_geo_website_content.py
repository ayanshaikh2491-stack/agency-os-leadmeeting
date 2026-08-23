from admin.workspace.agents import website as w
from admin.workspace.agents.content import _with_aeo_geo as c_with
from admin.agency import agent_aeo_geo

# Website: verify build_aeo_geo_section returns per-workspace content
for ws in ["Houston Plumbing Co", "Bright Smile Dental", "agency"]:
    sec = agent_aeo_geo.build_aeo_geo_section(ws)
    assert "AEO" in sec and "GEO" in sec, sec[:200]
    print(f"WEBSITE ctx OK for {ws}: {'Houston' in sec or 'agency' in sec or 'dental' in sec}")

# Content helper
c = c_with("BASE PROMPT", "Houston Plumbing Co")
assert "AEO" in c and "GEO" in c and "Houston" in c, c[:300]
print("CONTENT helper OK")

print("ALL_AEO_GEO_WIRING_OK")
