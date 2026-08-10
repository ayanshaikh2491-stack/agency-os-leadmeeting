#!/bin/bash
echo "=== STUCK PROCESSES ==="
ps aux | grep -E '_pb_gw|_gw_|pb_gateway|pb_gw' | grep -v grep
echo "=== ENV FILE ==="
cat /home/ubuntu/sba-backend/pb_gw_env.sh 2>/dev/null | sed 's/SERVICE_KEY=.*/SERVICE_KEY=<redacted>/'
echo "=== RUN SCRIPT ==="
cat /home/ubuntu/sba-backend/pb_gw_run.sh 2>/dev/null
echo "=== SSH SESSION CHECK (is shell responsive) ==="
echo "SHELL_OK"
