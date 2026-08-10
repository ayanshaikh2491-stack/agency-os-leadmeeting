#!/bin/bash
# Deep inspect: gateway errors, collections, import state
echo "=== GW LOG - errors with tracebacks ==="
grep -B2 -A15 "Traceback\|Error\|error" /home/ubuntu/sba-backend/pb_gw.log | tail -60
echo ""
echo "=== GW LOG - last 5 lines ==="
tail -5 /home/ubuntu/sba-backend/pb_gw.log
echo ""
echo "=== COLLECTIONS (via PB API) ==="
TOKEN=$(curl -s -m 5 -X POST http://127.0.0.1:8090/api/collections/_superusers/auth-with-password \
  -H 'Content-Type: application/json' \
  -d '{"identity":"admin@tagsagency.local","password":"pb-admin-2026-x9"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('token',''))" 2>/dev/null)
if [ -n "$TOKEN" ]; then
  echo "AUTH OK"
  curl -s -m 5 http://127.0.0.1:8090/api/collections?page=1&perPage=200 -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
d = json.load(sys.stdin)
for c in d.get('items', []):
    print(c['id'], c['name'], c.get('type',''))
"
else
  echo "AUTH FAILED"
fi
echo ""
echo "=== IMPORT LOG ==="
ls -la /home/ubuntu/pb_import.log 2>&1
tail -20 /home/ubuntu/pb_import.log 2>&1
echo ""
echo "=== SUPABASE CONTAINERS ==="
docker ps --format '{{.Names}} {{.Status}}' 2>&1 | head -20
