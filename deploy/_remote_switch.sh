#!/bin/bash
# Remote script: verify id fix, switch backend env, restart
set +e
echo "=== 1. id-sanitize test ==="
SRVKEY=$(grep -E '^SUPABASE_SERVICE_KEY=' /home/ubuntu/sba-backend/.env | sed 's/^SUPABASE_SERVICE_KEY=//' | tr -d '\r\n')
echo "KEYLEN=${#SRVKEY}"
curl -s -X POST http://127.0.0.1:8095/rest/v1/leads \
  -H "apikey: $SRVKEY" -H "Authorization: Bearer $SRVKEY" \
  -H "Content-Type: application/json" -H "Content-Profile: leads" \
  -d '{"id":"b0f3c1e2-0000-4000-8000-000000000099","name":"ec2-id-test","phone":"777"}' | head -c 400
echo ""

echo "=== 2. switch SUPABASE_URL ==="
grep -n 'SUPABASE_URL' /home/ubuntu/sba-backend/.env
sed -i 's|^SUPABASE_URL=.*|SUPABASE_URL=http://127.0.0.1:8095|' /home/ubuntu/sba-backend/.env
grep -n 'SUPABASE_URL' /home/ubuntu/sba-backend/.env

echo "=== 3. restart backend ==="
sudo systemctl restart sba.service
sleep 6
sudo systemctl is-active sba.service
