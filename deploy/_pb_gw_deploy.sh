#!/bin/bash
# Deploy pb_gateway.py on EC2 behind PocketBase, port 8095
set -e
cp /home/ubuntu/pb_gateway.py /home/ubuntu/sba-backend/pb_gateway.py 2>/dev/null || cp /home/ubuntu/_pb_gateway.py /home/ubuntu/sba-backend/pb_gateway.py
# Read SERVICE_KEY from backend .env (JWT)
SRVKEY=$(grep -E '^SUPABASE_SERVICE_KEY=' /home/ubuntu/sba-backend/.env | sed 's/^SUPABASE_SERVICE_KEY=//' | tr -d '\r\n')
echo "SERVICE_KEY length: ${#SRVKEY}"
# Kill any old gateway
pkill -f 'pb_gateway' 2>/dev/null || true
sleep 1
# Write a small env + launch script
cat > /home/ubuntu/sba-backend/pb_gw_run.sh <<EOF
#!/bin/bash
export PB_URL="http://127.0.0.1:8090"
export PB_ADMIN_EMAIL="admin@tagsagency.local"
export PB_ADMIN_PASS="pb-admin-2026-x9"
export SERVICE_KEY="$(printf '%s' "$SRVKEY")"
cd /home/ubuntu/sba-backend
exec /home/ubuntu/sba-backend/venv/bin/python -m uvicorn pb_gateway:app --host 127.0.0.1 --port 8095
EOF
chmod +x /home/ubuntu/sba-backend/pb_gw_run.sh
nohup bash /home/ubuntu/sba-backend/pb_gw_run.sh > /home/ubuntu/sba-backend/pb_gw.log 2>&1 &
sleep 3
echo "=== HEALTH ==="
curl -sf http://127.0.0.1:8095/api/health || echo "GATEWAY NOT UP"
echo ""
echo "=== LOG ==="
tail -5 /home/ubuntu/sba-backend/pb_gw.log
