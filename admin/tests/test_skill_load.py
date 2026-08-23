from admin.agency import seo_skills

print("registry:", [s["name"] for s in seo_skills.SEO_SKILL_REGISTRY])
m = seo_skills.detect_skills("i need answer engine optimization for chatgpt and ai search")
print("detected:", [x["name"] for x in m])
if m:
    c = m[0]["content"]
    print("content loaded (real not fallback):", "Skill:" not in c)
    print("first 200 chars:", c[:200])
