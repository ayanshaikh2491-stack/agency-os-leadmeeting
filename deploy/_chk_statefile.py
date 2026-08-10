"""Check enrichment state file on EC2."""
import json
import os
import time

path = os.path.join(os.getcwd(), ".sba_enrichment_state")
print("path:", path, "exists:", os.path.exists(path))
try:
    st = json.load(open(path))
    print("state entries:", len(st))
    now = time.time()
    recent = sum(1 for v in st.values() if now - float(v) < 24 * 3600)
    print("tried within 24h:", recent)
    items = sorted(st.items(), key=lambda kv: float(kv[1]), reverse=True)
    print("newest 3:", items[:3])
    print("oldest 3:", items[-3:])
except Exception as e:  # noqa: BLE001
    print("ERR", repr(e))
