path = r"deploy\deploy_sba.py"
src = open(path, encoding="utf-8").read()

old = (
    '    "admin/agency/ceo.py",\n'
    '    "admin/agency/social_skills.py",\n'
    '    "admin/agency/agent_persistence.py",\n'
    '    "admin/api/routes/sba.py",\n'
    '    "admin/api/routes/social.py",'
)
new = (
    '    "admin/agency/ceo.py",\n'
    '    "admin/agency/ceo_monitor.py",\n'
    '    "admin/agency/social_skills.py",\n'
    '    "admin/agency/agent_persistence.py",\n'
    '    "admin/api/routes/sba.py",\n'
    '    "admin/api/routes/ceo.py",\n'
    '    "admin/api/routes/social.py",'
)

count = src.count(old)
print("occurrences:", count)
if count != 2:
    print("UNEXPECTED count, aborting")
    raise SystemExit(1)

src = src.replace(old, new)
open(path, "w", encoding="utf-8").write(src)
print("REPLACED both FILES and COMPILE_FILES")
