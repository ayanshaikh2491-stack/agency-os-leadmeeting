#!/bin/bash
# Extract service key and write run script (no heredoc inside here, simple quoting)
SRVKEY=$(grep -E '^SUPABASE_SERVICE_KEY=' /home/ubuntu/sba-backend/.env | sed 's/^SUPABASE_SERVICE_KEY=//' | tr -d '\r\n')
echo "KEY_LEN=${#SRVKEY}"
echo "PB_URL=http://127.0.0.1:8090" > /home/ubuntu/sba-backend/pb_gw_env.sh
echo "PB_ADMIN_EMAIL=admin@tagsagency.local" >> /home/ubuntu/sba-backend/pb_gw_env.sh
echo "PB_ADMIN_PASS=pb-admin-2026-x9" >> /home/ubuntu/sba-backend/pb_gw_env.sh
echo "SERVICE_KEY=${SRVKEY}" >> /home/ubuntu/sba-backend/pb_gw_env.sh
ls -la /home/ubuntu/sba-backend/pb_gw_env.sh
echo "=== DONE ==="
