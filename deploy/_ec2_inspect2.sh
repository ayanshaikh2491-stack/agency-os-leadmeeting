#!/bin/bash
echo "=== DOCKER PS ==="
sudo docker ps --format '{{.Names}}\t{{.Status}}\t{{.Ports}}' 2>/dev/null
echo ""
echo "=== COMPOSE FILES ==="
find /home/ubuntu/supabase -maxdepth 3 -name '*.yml' -o -maxdepth 3 -name '*.yaml' 2>/dev/null | head
echo ""
echo "=== DB SERVICE NAME IN COMPOSE ==="
grep -E '^\s{2}[a-z0-9_-]+:' /home/ubuntu/supabase/docker/docker-compose.yml 2>/dev/null | head -30
echo ""
echo "=== PORT 8050 OWNER ==="
sudo ss -tlnp | grep 8050
echo ""
echo "=== PORT 8000 OWNER ==="
sudo ss -tlnp | grep 8000
echo ""
echo "=== ADMIN_PORT / env details ==="
grep -E '^(ADMIN_PORT|ADMIN_HOST|SUPABASE_URL|EC2_BACKEND_URL|DATABASE_URL)=' /home/ubuntu/sba-backend/.env 2>/dev/null
echo ""
echo "=== SBA SERVICE CONFIG ==="
systemctl cat sba.service 2>/dev/null | grep -E 'ExecStart|EnvironmentFile|WorkingDirectory'
echo ""
echo "=== BACKEND LOG TAIL ==="
sudo journalctl -u sba.service -n 5 --no-pager 2>/dev/null
