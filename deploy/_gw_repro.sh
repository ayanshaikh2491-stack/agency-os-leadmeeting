#!/bin/bash
# Reproduce import-style POST with real exported rows; capture gateway error bodies
SRVKEY=$(grep -E '^SUPABASE_SERVICE_KEY=' /home/ubuntu/sba-backend/.env | sed 's/^SUPABASE_SERVICE_KEY=//' | tr -d '\r\n')
echo "=== agents row 1 ==="
head -1 /home/ubuntu/pb_export/public__agents.jsonl
echo ""
echo "=== leads row 1 ==="
head -1 /home/ubuntu/pb_export/public__leads.jsonl | cut -c1-400
echo ""
echo "=== ws_agency leads row 1 ==="
head -1 /home/ubuntu/pb_export/ws_agency__leads.jsonl | cut -c1-400
echo ""
echo "=== POST real agents row via gateway ==="
head -1 /home/ubuntu/pb_export/public__agents.jsonl > /tmp/agent_row.json
curl -s -m 15 -X POST http://127.0.0.1:8095/rest/v1/agents \
  -H "apikey: $SRVKEY" -H "Authorization: Bearer $SRVKEY" \
  -H "Content-Type: application/json" -H "Prefer: return=representation" \
  --data-binary @/tmp/agent_row.json -w "\nHTTP:%{http_code}\n" | tail -3
echo "=== POST real leads row via gateway (public) ==="
head -1 /home/ubuntu/pb_export/public__leads.jsonl > /tmp/lead_row.json
curl -s -m 15 -X POST http://127.0.0.1:8095/rest/v1/leads \
  -H "apikey: $SRVKEY" -H "Authorization: Bearer $SRVKEY" \
  -H "Content-Type: application/json" -H "Prefer: return=representation" \
  --data-binary @/tmp/lead_row.json -w "\nHTTP:%{http_code}\n" | tail -3
echo "=== POST real ws_agency leads row via gateway ==="
head -1 /home/ubuntu/pb_export/ws_agency__leads.jsonl > /tmp/wslead_row.json
curl -s -m 15 -X POST http://127.0.0.1:8095/rest/v1/leads \
  -H "apikey: $SRVKEY" -H "Authorization: Bearer $SRVKEY" \
  -H "Content-Type: application/json" -H "Prefer: return=representation" \
  -H "Content-Profile: ws_agency" \
  --data-binary @/tmp/wslead_row.json -w "\nHTTP:%{http_code}\n" | tail -3
