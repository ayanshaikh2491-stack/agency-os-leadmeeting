import json, collections, os

cands = json.load(open("data/sba_maps_candidates.json", encoding="utf-8"))
print("candidates total:", len(cands))
print("status dist:", collections.Counter(c.get("status", "?") for c in cands).most_common(12))

for p in ["data/sba_maps_leads_good.jsonl", "data/sba_maps_leads_live.jsonl", "data/sba_maps_leads.csv"]:
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            n = sum(1 for _ in f)
        print(p, "->", n, "lines", os.path.getsize(p), "bytes")

# good leads detail
good = []
if os.path.exists("data/sba_maps_leads_good.jsonl"):
    for line in open("data/sba_maps_leads_good.jsonl", encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            good.append(json.loads(line))
        except json.JSONDecodeError:
            pass
print("\nGOOD leads:", len(good))
for g in good:
    print("  ", g.get("name"), "|", g.get("category"), "|", g.get("city_state"), "|", g.get("phone"))
