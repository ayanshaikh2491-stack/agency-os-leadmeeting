#!/bin/bash
# Remote: compare Supabase vs PocketBase counts, then restart autopilot
set +e
SRVKEY=$(grep -E '^SUPABASE_SERVICE_KEY=' /home/ubuntu/sba-backend/.env | sed 's/^SUPABASE_SERVICE_KEY=//' | tr -d '\r\n')

echo "=== Supabase (8050) counts ==="
for t in leads agents workspaces goals clients org_charts; do
  C=$(curl -s -m 10 "http://127.0.0.1:8050/rest/v1/$t?select=id&limit=0" -H "apikey: $SRVKEY" -H "Authorization: Bearer $SRVKEY" -H "Prefer: count=exact" -D - -o /dev/null 2>/dev/null | grep -i content-range | sed 's/.*\///')
  echo "  $t: $C"
done

echo ""
echo "=== PocketBase (via gateway 8095) counts ==="
for t in leads agents workspaces goals clients org_charts; do
  C=$(curl -s -m 10 "http://127.0.0.1:8095/rest/v1/$t?select=id&limit=0" -H "apikey: $SRVKEY" -H "Authorization: Bearer $SRVKEY" -H "Prefer: count=exact" -D - -o /dev/null 2>/dev/null | grep -i content-range | sed 's/.*\///')
  echo "  $t: $C"
done

echo ""
echo "=== ws_agency__leads counts ==="
echo "  Supabase: $(curl -s -m 10 'http://127.0.0.1:8050/rest/v1/leads?select=id&limit=0' -H "apikey: $SRVKEY" -H "Authorization: Bearer $SRVKEY" -H "Prefer: count=exact" -H 'Content-Profile: ws_agency' -D - -o /dev/null 2>/dev/null | grep -i content-range | sed 's/.*\///')"
echo "  PB:       $(curl -s -m 10 'http://127.0.0.1:8095/rest/v1/leads?select=id&limit=0' -H "apikey: $SRVKEY" -H "Authorization: Bearer $SRVKEY" -H "Prefer: count=exact" -H 'Content-Profile: ws_agency' -D - -o /dev/null 2>/dev/null | grep -i content-range | sed 's/.*\///')"
