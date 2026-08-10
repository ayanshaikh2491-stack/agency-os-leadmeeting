#!/bin/bash
echo '=== SUPABASE DIR ==='
ls -d /home/ubuntu/*supabase* /srv/*supabase* /opt/*supabase* /home/ubuntu/sba-backend/supabase* 2>/dev/null
echo '=== DOCKER COMPOSE FILES ==='
find /home/ubuntu /srv /opt -maxdepth 3 -name 'docker-compose*.yml' -o -maxdepth 3 -name 'compose.yaml' 2>/dev/null | head -20
echo '=== SUPABASE ENV ==='
sudo find / -maxdepth 4 -name '.env' -path '*supabase*' 2>/dev/null | head -5
echo '=== RALLLY DIR ==='
find /home/ubuntu /srv /opt -maxdepth 3 -iname '*rallly*' -type d 2>/dev/null | head -5
echo '=== BACKEND ENV (supabase URL refs) ==='
sudo grep -rIl 'SUPABASE' /home/ubuntu/sba-backend/.env 2>/dev/null | head -3
echo '=== DATA SIZE (postgres volume) ==='
sudo du -sh /var/lib/docker/volumes/*supabase* 2>/dev/null | head -10
echo '=== DOCKER VOLUMES LIST ==='
sudo docker volume ls --format '{{.Name}}' 2>/dev/null | head -20
