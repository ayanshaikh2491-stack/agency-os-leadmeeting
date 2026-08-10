#!/bin/bash
# Simple gateway launcher - no env passing needed, gateway reads backend .env
set +e
pkill -f 'uvicorn pb_gateway' 2>/dev/null
sleep 1
cd /home/ubuntu/sba-backend
export PB_URL="http://127.0.0.1:8090"
export PB_ADMIN_EMAIL="admin@tagsagency.local"
export PB_ADMIN_PASS="pb-admin-2026-x9"
export PB_ENV_FILE="/home/ubuntu/sba-backend/.env"
nohup /home/ubuntu/sba-backend/venv/bin/python -m uvicorn pb_gateway:app --host 127.0.0.1 --port 8095 \
  > /home/ubuntu/sba-backend/pb_gw.log 2>&1 &
echo "STARTED PID $!"
sleep 4
curl -sf http://127.0.0.1:8095/api/health && echo " HEALTH_OK" || echo "NOT_UP"
echo "=== LOG ==="
tail -10 /home/ubuntu/sba-backend/pb_gw.log
