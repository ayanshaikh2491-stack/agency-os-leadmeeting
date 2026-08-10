#!/bin/bash
# Data audit on EC2: verify no silent table split + email distribution parity
set -u
PB=http://127.0.0.1:8090
TOKEN=$(curl -s -X POST $PB/api/collections/_superusers/auth-with-password \
  -H 'Content-Type: application/json' \
  -d '{"identity":"admin@tagsagency.local","password":"pb-admin-2026-x9"}' \
  | python3 -c 'import sys,json; print(json.load(sys.stdin).get("token",""))')

auth="Authorization: Bearer $TOKEN"

count() { # $1 collection
  curl -s -H "$auth" "$PB/api/collections/$1/records?perPage=1" \
    | python3 -c 'import sys,json; print(json.load(sys.stdin).get("totalItems",0))'
}

echo "=== counts ==="
for c in leads leads__leads ws_agency__leads ws_agency__agent_memory ws_agency__agent_checkpoints; do
  printf "%-28s %s\n" "$c" "$(count $c)"
done

echo "=== leads: email + workspace distribution ==="
curl -s -H "$auth" "$PB/api/collections/leads/records?perPage=200" > /tmp/leads1.json
python3 - <<'EOF'
import json, collections
rows=[]
for i in (1,2):
    try:
        rows += json.load(open(f"/tmp/leads{i}.json")).get("items",[])
    except Exception: pass
total=len(rows)
has_email=sum(1 for r in rows if str(r.get("email") or "").strip())
ws=collections.Counter(str(r.get("workspace_name") or "(none)") for r in rows)
print("sampled leads:", total)
print("with email:", has_email, "| without email:", total-has_email)
print("workspaces:", dict(ws))
EOF

echo "=== leads__leads: same distribution (split check) ==="
curl -s -H "$auth" "$PB/api/collections/leads__leads/records?perPage=200" > /tmp/leadsx.json
python3 - <<'EOF'
import json, collections
rows=[]
try:
    rows = json.load(open("/tmp/leadsx.json")).get("items",[])
except Exception as e:
    print("err", e)
total=len(rows)
has_email=sum(1 for r in rows if str(r.get("email") or "").strip())
ws=collections.Counter(str(r.get("workspace_name") or "(none)") for r in rows)
print("sampled leads__leads:", total)
print("with email:", has_email, "| without email:", total-has_email)
print("workspaces:", dict(ws))
EOF
