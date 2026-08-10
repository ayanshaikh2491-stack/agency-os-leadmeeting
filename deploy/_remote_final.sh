#!/bin/bash
# Remote: final verification + autopilot restart
set +e
echo "=== PB counts (direct 8090) ==="
TOKEN=$(curl -s -X POST http://127.0.0.1:8090/api/collections/_superusers/auth-with-password -H 'Content-Type: application/json' -d '{"identity":"admin@tagsagency.local","password":"pb-admin-2026-x9"}' | python3 -c 'import sys,json; print(json.load(sys.stdin).get("token",""))' 2>/dev/null)
for c in leads agents workspaces goals clients org_charts ws_agency__leads ws_agency__website_builds ws_agency__website_docs ws_agency__website_build_log; do
  N=$(curl -s -m 10 "http://127.0.0.1:8090/api/collections/$c/records?perPage=1" -H "Authorization: Bearer $TOKEN" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("totalItems","ERR"))' 2>/dev/null)
  echo "  $c: $N"
done

echo ""
echo "=== Supabase counts (8050) ==="
SRVKEY=$(grep -E '^SUPABASE_SERVICE_KEY=' /home/ubuntu/sba-backend/.env | sed 's/^SUPABASE_SERVICE_KEY=//' | tr -d '\r\n')
for t in leads agents workspaces goals clients org_charts; do
  C=$(curl -s -m 10 "http://127.0.0.1:8050/rest/v1/$t?select=id&limit=0" -H "apikey: $SRVKEY" -H "Authorization: Bearer $SRVKEY" -H "Prefer: count=exact" -D - -o /dev/null 2>/dev/null | grep -i content-range | sed 's/.*\///')
  echo "  $t: $C"
done

echo ""
echo "=== restart autopilot (pick up new gateway env) ==="
sudo systemctl restart sba-autopilot.service
sleep 8
sudo systemctl is-active sba-autopilot.service
echo ""
echo "=== autopilot fresh logs ==="
sudo journalctl -u sba-autopilot.service --since '30 seconds ago' --no-pager | tail -15
