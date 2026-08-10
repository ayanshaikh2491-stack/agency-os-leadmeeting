#!/bin/bash
echo '=== ALL DOCKER VOLUMES ==='
sudo docker volume ls --format '{{.Name}} {{.Driver}}'
echo '=== SUPABASE DB DATA SIZE ==='
sudo du -sh /var/lib/docker/volumes/supabase_db-data 2>/dev/null || echo 'no supabase_db-data volume'
echo '=== POSTGRES DB SIZE (live) ==='
cd /home/ubuntu/supabase && sudo docker compose -f docker/docker-compose.yml ps --format '{{.Name}} {{.Status}}' 2>/dev/null | head -20
echo '=== COMPOSE PROJECT NAME ==='
sudo docker inspect --format '{{ index .Config.Labels "com.docker.compose.project" }}' supabase-db 2>/dev/null || echo 'unknown'
echo '=== SUPABASE VERSION ==='
sudo grep -E 'supabase/postgres:' /home/ubuntu/supabase/docker/docker-compose.yml | head -2
echo '=== RALLLY COMPOSE HEAD ==='
head -30 /home/ubuntu/rallly/docker-compose.yml
echo '=== BACKEND ENV SUPABASE KEYS (masked) ==='
sudo grep -E 'SUPABASE_URL|SUPABASE_KEY|SUPABASE_ANON|SUPABASE_SERVICE' /home/ubuntu/sba-backend/.env 2>/dev/null | sed 's/=\(.\{12\}\).*/=\1***MASKED***/' | head -10
echo '=== DISK ROOM ==='
df -h / | tail -1
