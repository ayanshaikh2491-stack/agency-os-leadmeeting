#!/bin/bash
echo "=== GATEWAY PROCESS ==="
ps aux | grep -E 'pb_gw|uvicorn.*8095' | grep -v grep | head
echo "=== PORT 8095 ==="
sudo ss -tlnp | grep 8095
echo "=== HEALTH ==="
curl -sf http://127.0.0.1:8095/api/health || echo "NOT UP"
echo ""
echo "=== GW LOG ==="
tail -15 /home/ubuntu/sba-backend/pb_gw.log 2>/dev/null || echo "no log"
echo "=== RUN SCRIPT ==="
cat /home/ubuntu/sba-backend/pb_gw_run.sh 2>/dev/null | head -10
