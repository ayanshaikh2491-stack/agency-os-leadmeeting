import json, collections, os

live = []
for line in open("data/sba_maps_leads_live.jsonl", encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    try:
        live.append(json.loads(line))
    except json.JSONDecodeError:
        pass

print("live total:", len(live))
print("with phone:", sum(1 for d in live if d.get("phone")))
print("no phone:", sum(1 for d in live if not d.get("phone")))
print("website_status dist:", collections.Counter(d.get("website_status", "?") for d in live).most_common())
print("mode dist:", collections.Counter(d.get("mode", "?") for d in live).most_common())
print("has_website field dist:", collections.Counter(bool(d.get("has_website")) for d in live).most_common())

# those with phone AND verified_none = already confirmed good
good_ready = [d for d in live if d.get("phone") and d.get("website_status") == "verified_none"]
print("\nalready-confirmed good (phone + verified_none):", len(good_ready))
for d in good_ready[:15]:
    print("  ", d.get("name"), "|", d.get("category"), "|", d.get("city_state"), "|", d.get("phone"))

# duplicate check against good.jsonl
good_existing = set()
for line in open("data/sba_maps_leads_good.jsonl", encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    try:
        good_existing.add(json.loads(line).get("href", ""))
    except json.JSONDecodeError:
        pass
print("\ngood.jsonl existing hrefs:", len(good_existing))
new_from_live = [d for d in good_ready if d.get("href") not in good_existing]
print("new good candidates from live (not in good.jsonl):", len(new_from_live))
