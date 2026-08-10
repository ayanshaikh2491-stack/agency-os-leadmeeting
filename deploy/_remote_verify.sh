#!/bin/bash
# Remote: verify backend end-to-end through gateway
set +e
echo "=== backend health (port 8000) ==="
curl -s -m 10 http://127.0.0.1:8000/api/health | head -c 300
echo ""
curl -s -m 10 http://127.0.0.1:8000/health | head -c 300
echo ""

echo "=== backend logs (last errors) ==="
sudo journalctl -u sba.service --since '5 minutes ago' --no-pager 2>/dev/null | grep -iE 'error|traceback|exception' | tail -15
echo "--- last 10 lines ---"
sudo journalctl -u sba.service --since '5 minutes ago' --no-pager 2>/dev/null | tail -10

echo "=== gateway log: any recent 500s? ==="
tail -20 /home/ubuntu/sba-backend/pb_gw.log 2>/dev/null | grep -E '500|POST|GET' | tail -15

echo "=== direct PB count check via gateway ==="
SRVKEY=$(grep -E '^SUPABASE_SERVICE_KEY=' /home/ubuntu/sba-backend/.env | sed 's/^SUPABASE_SERVICE_KEY=//' | tr -d '\r\n')
curl -s -m 10 "http://127.0.0.1:8095/rest/v1/leads?select=count" -H "apikey: $SRVKEY" -H "Authorization: Bearer $SRVKEY" | head -c 200
echo ""
