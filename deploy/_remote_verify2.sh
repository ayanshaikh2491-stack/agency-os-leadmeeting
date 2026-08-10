#!/bin/bash
# Remote: check if 500s are recent and what fails
set +e
echo "=== last 30 lines of pb_gw.log ==="
tail -30 /home/ubuntu/sba-backend/pb_gw.log

echo ""
echo "=== count of 500s by minute (last 200 lines) ==="
tail -200 /home/ubuntu/sba-backend/pb_gw.log | grep -c ' 500 '

echo "=== backend log: what does backend call that 500s? ==="
sudo journalctl -u sba.service --since '10 minutes ago' --no-pager 2>/dev/null | grep -iE '500|error|traceback|leads' | tail -30
