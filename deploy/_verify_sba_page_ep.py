"""Verify all SBA page GET endpoints through Vercel proxy."""
import json, urllib.request, urllib.error

BASE = "https://agency-frontend-seven.vercel.app"
paths = ["/api/sba/status", "/api/sba/pipeline", "/api/sba/meetings", "/api/sba/finance",
         "/api/sba/leads", "/api/sba/skills", "/api/sba/handoffs", "/api/sba/workspaces",
         "/api/sba/reasoning", "/api/sba/strategy", "/api/agents"]

for p in paths:
    try:
        with urllib.request.urlopen(BASE + p, timeout=30) as resp:
            raw = resp.read().decode()
            print(f"{p}: {resp.status} {raw[:80]}")
    except urllib.error.HTTPError as e:
        print(f"{p}: {e.code} {e.read().decode()[:120]}")
    except Exception as e:
        print(f"{p}: ERR {str(e)[:120]}")
