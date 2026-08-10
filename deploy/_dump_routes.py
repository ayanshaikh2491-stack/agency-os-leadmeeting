import os, sys
sys.path.insert(0, "/home/ubuntu/sba-backend")
from admin.main import app
for route in app.routes:
    p = getattr(route, "path", "")
    if "/api/agents" in p or "/api/sba" in p:
        print(sorted(getattr(route, "methods", []) or []), p)
