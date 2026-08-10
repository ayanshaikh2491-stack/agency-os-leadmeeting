#!/bin/bash
# Launch gateway from env file, detached properly
set +e
pkill -f 'uvicorn pb_gateway' 2>/dev/null
sleep 1
cd /home/ubuntu/sba-backend
# Source env file (it has KEY=VAL lines) then launch with setsid so ssh doesn't hang
setsid env $(grep -v '^#' /home/ubuntu/sba-backend/pb_gw_env.sh | xargs) \
  /home/ubuntu/sba-backend/venv/bin/python -m uvicorn pb_gateway:app --host 127.0.0.1 --port 8095 \
  > /home/ubuntu/sba-backend/pb_gw.log 2>&1 < /dev/null &
disown
echo "LAUNCHED"
exit 0
