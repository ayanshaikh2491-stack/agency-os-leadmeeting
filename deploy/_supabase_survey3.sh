#!/bin/bash
echo '=== SUPABASE-DB MOUNTS ==='
sudo docker inspect supabase-db --format '{{range .Mounts}}{{.Type}} {{.Source}} -> {{.Destination}}{{println}}{{end}}' 2>/dev/null
echo '=== ALL VOLUMES (sudo) ==='
sudo docker volume ls 2>/dev/null
echo '=== VOLUMES ACTUALLY USED ==='
sudo docker ps -a --format '{{.Names}}' | while read c; do
  sudo docker inspect "$c" --format '{{range .Mounts}}{{if eq .Type "volume"}}{{.Name}} {{end}}{{end}}' 2>/dev/null | tr ' ' '\n' | grep -v '^$' | sed "s/^/$c: /"
done | sort -u | head -40
echo '=== DOCKER ROOT ==='
sudo docker info --format '{{.DockerRootDir}}' 2>/dev/null
echo '=== COMPOSE VOLUMES SECTION ==='
sudo grep -A 20 '^volumes:' /home/ubuntu/supabase/docker/docker-compose.yml | head -30
echo '=== DB-DATA BIND MOUNT CHECK ==='
sudo grep -B 2 -A 6 'db-data\|POSTGRES_DATA' /home/ubuntu/supabase/docker/docker-compose.yml | head -40
