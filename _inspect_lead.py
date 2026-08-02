import json
lines = [json.loads(l) for l in open(r"C:\Users\TAUSHEF\Downloads\int\data\sba_maps_leads_good.jsonl", encoding="utf-8")]
print(json.dumps(lines[0], indent=1, default=str)[:1800])
print("\n--- keys:", list(lines[0].keys()))
