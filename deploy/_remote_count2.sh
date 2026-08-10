#!/bin/bash
# Remote: compare counts via direct PB API (totalItems)
set +e
TOKEN=$(curl -s -X POST http://127.0.0.1:8090/api/collections/_superusers/auth-with-password -H 'Content-Type: application/json' -d '{"identity":"admin@tagsagency.local","password":"pb-admin-2026-x9"}' | python3 -c 'import sys,json; print(json.load(sys.stdin).get("token",""))' 2>/dev/null)
echo "TOKEN_LEN=${#TOKEN}"

echo "=== PocketBase totalItems (direct 8090) ==="
for c in leads agents workspaces goals clients org_charts ws_agency__leads ws_agency__website_builds ws_agency__website_docs ws_agency__website_build_log; do
  N=$(curl -s -m 10 "http://127.0.0.1:8090/api/collections/$c/records?perPage=1" -H "Authorization: Bearer $TOKEN" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("totalItems","ERR"))' 2>/dev/null)
  echo "  $c: $N"
done

echo ""
echo "=== gateway counts (should equal Supabase) ==="
SRVKEY=$(grep -E '^SUPABASE_SERVICE_KEY=' /home/ubuntu/sba-backend/.env | sed 's/^SUPABASE_SERVICE_KEY=//' | tr -d '\r\n')
for t in leads agents workspaces goals clients org_charts; do
  # GET all (paginated 200) and count via python
  N=$(curl -s -m 15 "http://127.0.0.1:8095/rest/v1/$t?select=id&limit=200" -H "apikey: $SRVKEY" -H "Authorization: Bearer $SRVKEY" | python3 -c 'import sys,json; print(len(json.load(sys.stdin)))' 2>/dev/null)
  echo "  $t: $N"
done
