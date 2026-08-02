import json, sys
from collections import Counter

path = "data/sba_maps_leads_live.jsonl"
with_phone = []
no_phone = []
for line in open(path, encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    d = json.loads(line)
    if d.get("phone"):
        with_phone.append(d)
    else:
        no_phone.append(d)

print(f"TOTAL: {len(with_phone) + len(no_phone)}")
print(f"WITH phone+addr (solid): {len(with_phone)}")
print(f"NO phone (suspicious):  {len(no_phone)}")
print()
print("=== Categories of suspicious ===")
for cat, n in Counter(d["category"] for d in no_phone).most_common():
    print(f"  {cat}: {n}")
