#!/bin/bash
# Check gateway version diff + import state
echo "=== DEPLOYED GW MD5 ==="
md5sum /home/ubuntu/sba-backend/pb_gateway.py
echo "=== GW LOG - when did 500s happen (timestamps around them) ==="
grep -n "500\|Traceback\|ERROR" /home/ubuntu/sba-backend/pb_gw.log | head -10
echo "=== GW LOG - first 20 lines ==="
head -20 /home/ubuntu/sba-backend/pb_gw.log
echo "=== PB DATA: collection counts via gateway ==="
SRVKEY=$(grep -E '^SUPABASE_SERVICE_KEY=' /home/ubuntu/sba-backend/.env | sed 's/^SUPABASE_SERVICE_KEY=//' | tr -d '\r\n')
echo "--- public leads ---"
curl -s -m 10 "http://127.0.0.1:8095/rest/v1/leads?select=id&limit=0" -H "apikey: $SRVKEY" -H "Authorization: Bearer $SRVKEY" -w "\nHTTP:%{http_code}\n" | tail -2
echo "--- ws_agency leads ---"
curl -s -m 10 "http://127.0.0.1:8095/rest/v1/leads?select=id&limit=0" -H "apikey: $SRVKEY" -H "Authorization: Bearer $SRVKEY" -H "Content-Profile: ws_agency" -w "\nHTTP:%{http_code}\n" | tail -2
echo "--- recent public leads (should show TEST-GW-PROBE rows) ---"
curl -s -m 10 "http://127.0.0.1:8095/rest/v1/leads?select=business_name,phone&order=created_at.desc&limit=5" -H "apikey: $SRVKEY" -H "Authorization: Bearer $SRVKEY" -w "\nHTTP:%{http_code}\n"
