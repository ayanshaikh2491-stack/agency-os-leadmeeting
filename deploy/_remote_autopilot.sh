#!/bin/bash
# Remote: verify autopilot is working through gateway
set +e
echo "=== autopilot status ==="
sudo systemctl is-active sba-autopilot.service

echo ""
echo "=== autopilot recent activity (last 25 lines) ==="
sudo journalctl -u sba-autopilot.service --no-pager -n 25 | tail -25

echo ""
echo "=== leads in PocketBase (via gateway) ==="
SRVKEY=$(grep -E '^SUPABASE_SERVICE_KEY=' /home/ubuntu/sba-backend/.env | sed 's/^SUPABASE_SERVICE_KEY=//' | tr -d '\r\n')
curl -s -m 10 "http://127.0.0.1:8095/rest/v1/leads?select=name,status&order=created_at.desc&limit=5" -H "apikey: $SRVKEY" -H "Authorization: Bearer $SRVKEY" | head -c 800
echo ""

echo ""
echo "=== all collection counts via direct PB ==="
TOKEN=$(curl -s -X POST http://127.0.0.1:8090/api/collections/_superusers/auth-with-password -H 'Content-Type: application/json' -d '{"identity":"admin@tagsagency.local","password":"pb-admin-2026-x9"}' | python3 -c 'import sys,json; print(json.load(sys.stdin).get("token",""))' 2>/dev/null)
for c in leads agents ws_agency__leads ws_agency__website_builds ws_agency__website_docs ws_agency__website_build_log; do
  N=$(curl -s "http://127.0.0.1:8090/api/collections/$c/records?perPage=1" -H "Authorization: Bearer $TOKEN" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("totalItems","ERR"))' 2>/dev/null)
  echo "$c: $N"
done
