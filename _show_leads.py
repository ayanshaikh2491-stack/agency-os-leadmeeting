import json, sys

path = "data/sba_maps_leads_live.jsonl"
n = int(sys.argv[1]) if len(sys.argv) > 1 else 60
try:
    lines = open(path, encoding="utf-8").readlines()
except FileNotFoundError:
    print("No live file yet")
    sys.exit(0)

print(f"=== {len(lines)} verified leads so far (showing {min(n, len(lines))}) ===\n")
for line in lines[-n:]:
    line = line.strip()
    if not line:
        continue
    try:
        d = json.loads(line)
    except json.JSONDecodeError:
        continue
    name = d.get("name", "?")
    cat = d.get("category", "?")
    cst = d.get("city_state", "?")
    phone = d.get("phone") or "no-phone"
    addr = (d.get("address") or "").strip()
    print(f"  {name} | {cat} | {cst} | {phone} | {addr}")
