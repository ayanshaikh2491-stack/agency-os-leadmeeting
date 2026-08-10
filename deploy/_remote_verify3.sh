#!/bin/bash
# Remote: check NEW gateway (systemd) logs for 500s
set +e
echo "=== gateway service status ==="
sudo systemctl status sba-gateway.service --no-pager | head -15

echo ""
echo "=== gateway journal since start (last 40 lines) ==="
sudo journalctl -u sba-gateway.service --no-pager -n 40 | tail -40

echo ""
echo "=== gateway journal: 500 count since start ==="
sudo journalctl -u sba-gateway.service --no-pager | grep -c ' 500 '
