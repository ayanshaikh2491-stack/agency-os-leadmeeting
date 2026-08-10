#!/bin/bash
# Reproduce gateway POST error and capture response body
set -x
# 1. service key from backend .env
SRVKEY=$(grep -E '^SUPABASE_SERVICE_KEY=' /home/ubuntu/sba-backend/.env | sed 's/^SUPABASE_SERVICE_KEY=//' | tr -d '\r\n')
echo "SRVKEY len: ${#SRVKEY}"
echo "=== POST /rest/v1/leads (minimal) ==="
curl -s -m 10 -X POST http://127.0.0.1:8095/rest/v1/leads \
  -H "apikey: $SRVKEY" \
  -H "Authorization: Bearer $SRVKEY" \
  -H "Content-Type: application/json" \
  -H "Content-Profile: ws_agency" \
  -d '{"business_name":"TEST-GW-PROBE","phone":"0000000000"}' -w "\nHTTP_CODE:%{http_code}\n"
echo "=== POST /rest/v1/leads (public profile, no profile header) ==="
curl -s -m 10 -X POST http://127.0.0.1:8095/rest/v1/leads \
  -H "apikey: $SRVKEY" \
  -H "Authorization: Bearer $SRVKEY" \
  -H "Content-Type: application/json" \
  -d '{"business_name":"TEST-GW-PROBE2","phone":"0000000001"}' -w "\nHTTP_CODE:%{http_code}\n"
echo "=== GW LOG TAIL ==="
tail -5 /home/ubuntu/sba-backend/pb_gw.log
