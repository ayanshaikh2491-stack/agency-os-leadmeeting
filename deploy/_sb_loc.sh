#!/bin/bash
echo "=== supabase dir ==="
ls -la /home/ubuntu/supabase/ 2>/dev/null | head -20
echo "=== compose files ==="
find /home/ubuntu/supabase -maxdepth 3 -name 'docker-compose*.yml' 2>/dev/null | head
echo "=== env files ==="
find /home/ubuntu/supabase -maxdepth 2 -name '.env' 2>/dev/null | head
echo "=== docker ps supabase containers ==="
docker ps --format "table {{.Names}}\t{{.Image}}" 2>/dev/null | grep -iE "supabase|rallly|NAMES" | head -20
