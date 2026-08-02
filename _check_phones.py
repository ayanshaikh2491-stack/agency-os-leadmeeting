import json, os

BASE = r"C:\Users\TAUSHEF\Downloads\int"
lines = [json.loads(l) for l in open(os.path.join(BASE, "data", "sba_maps_leads_live.jsonl"), encoding="utf-8")]
with_phone = [l for l in lines if l.get("phone")]
print("total:", len(lines), "with phone:", len(with_phone))

# Show a few
for l in with_phone[:3]:
    print(repr(l.get("phone")), "|", l.get("name"))

# Show P V Auto
for l in lines:
    if l.get("name") == "P V Auto Services":
        print("PV keys:", {k: l.get(k) for k in l.keys()})
