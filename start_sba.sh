#!/bin/bash
# SBA Backend startup script - runs on EC2
cd /home/ubuntu/sba-backend
export PYTHONPATH=/home/ubuntu/sba-backend
pkill -f "admin.main" 2>/dev/null
sleep 1
/home/ubuntu/sba-backend/venv/bin/python -m admin.main > /tmp/sba.log 2>&1 &
echo "Started PID=$!"
sleep 4
curl -s --max-time 5 http://localhost:9002/api/health
echo ""
echo "--- Log ---"
tail -10 /tmp/sba.log
