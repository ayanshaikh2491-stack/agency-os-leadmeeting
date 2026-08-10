#!/bin/bash
# Remote: check autopilot env and import state
set +e
echo "=== autopilot PID start time ==="
ps -o pid,lstart,cmd -p 3409871 2>/dev/null

echo ""
echo "=== autopilot env SUPABASE_URL ==="
sudo cat /proc/3409871/environ 2>/dev/null | tr '\0' '\n' | grep -E '^SUPABASE_URL=' | head -2
echo "(if empty, reads .env at call time)"

echo ""
echo "=== Supabase docker leads count (old data source) ==="
SRVKEY=$(grep -E '^SUPABASE_SERVICE_KEY=' /home/ubuntu/sba-backend/.env | sed 's/^SUPABASE_SERVICE_KEY=//' | tr -d '\r\n')
curl -s -m 10 "http://127.0.0.1:8050/rest/v1/leads?select=id&limit=0" -H "apikey: $SRVKEY" -H "Authorization: Bearer $SRVKEY" -H "Prefer: count=exact" -D - -o /dev/null 2>/dev/null | grep -i content-range | head -2

echo ""
echo "=== import script exists? ==="
ls -la /home/ubuntu/sba-backend/_pb_import.py 2>/dev/null
head -40 /home/ubuntu/sba-backend/_pb_import.py 2>/dev/null

echo ""
echo "=== recent autopilot restart history ==="
sudo journalctl -u sba-autopilot.service --no-pager | grep -E 'Started|Stopped|Stopping' | tail -5
