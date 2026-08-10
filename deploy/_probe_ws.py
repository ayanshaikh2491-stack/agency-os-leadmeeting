"""Run on EC2: dump workspace config + DB lead source counts."""
import json, sys
sys.path.insert(0, ".")
from collections import Counter

try:
    from admin.agency.sba_biztypes import get_workspace_config, list_sba_workspaces
    ws = list_sba_workspaces()
    print("WORKSPACES:", json.dumps(ws)[:600])
except Exception as e:
    print("WS ERR:", repr(e)[:300])

try:
    cfg = get_workspace_config("agency")
    print("CFG:", json.dumps(cfg, default=str)[:800])
except Exception as e:
    print("CFG ERR:", repr(e)[:300])

try:
    from admin.agency.sba_pipeline import supabase_config, load_leads
    u, k = supabase_config()
    ls = load_leads(u, k)
    print("TOTAL:", len(ls))
    print("SOURCES:", dict(Counter((l.get("source") or "unknown") for l in ls)))
    print("CATS:", dict(Counter((l.get("category") or "unknown") for l in ls).most_common(10)))
    print("RECENT:", [((l.get("created_at") or l.get("ts") or "")[:16], l.get("name"), l.get("source")) for l in ls[-5:]])
except Exception as e:
    print("DB ERR:", repr(e)[:300])
