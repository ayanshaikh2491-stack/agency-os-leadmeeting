#!/bin/bash
# Inspect PocketBase + gateway state on EC2
echo "=== PROCS ==="
ps aux | grep -E 'pocketbase|pb_gateway|uvicorn' | grep -v grep
echo "=== PB LOG ==="
tail -20 /home/ubuntu/pocketbase/pb_serve.log
echo "=== GW LOG ==="
tail -30 /home/ubuntu/sba-backend/pb_gw.log
echo "=== GW ENV/RUN ==="
ls -la /home/ubuntu/sba-backend/pb_gw_run.sh 2>&1
ls -la /home/ubuntu/pb_gateway.py 2>&1
echo "=== PB API 8090 ==="
curl -s -m 5 http://127.0.0.1:8090/api/health || echo "PB DOWN"
echo ""
echo "=== GW API 8095 ==="
curl -s -m 5 http://127.0.0.1:8095/api/health || echo "GW DOWN"
echo ""
