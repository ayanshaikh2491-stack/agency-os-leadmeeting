#!/bin/bash
# ============================================================
# migrate_supabase.sh — Supabase + Rallly migration to new EC2
# Run ONCE on the NEW instance (target) after it's up.
# Usage: bash migrate_supabase.sh <old_ip>
# ============================================================
set -euo pipefail
OLD_IP="${1:?Usage: bash migrate_supabase.sh <old_ip>}"
echo "=== [1/8] Installing docker + compose ==="
sudo apt-get update -y -qq
sudo apt-get install -y -qq docker.io docker-compose-v2 rsync 2>/dev/null || sudo apt-get install -y -qq docker.io rsync
sudo systemctl enable --now docker
sudo usermod -aG docker ubuntu

echo "=== [2/8] Copying supabase + rallly configs ==="
rsync -az --progress ubuntu@${OLD_IP}:/home/ubuntu/supabase/ /home/ubuntu/supabase/
rsync -az --progress ubuntu@${OLD_IP}:/home/ubuntu/rallly/ /home/ubuntu/rallly/
chown -R ubuntu:ubuntu /home/ubuntu/supabase /home/ubuntu/rallly

echo "=== [3/8] Building postgres volume dir ==="
mkdir -p /home/ubuntu/supabase/docker/volumes/db/data
chown -R 999:999 /home/ubuntu/supabase/docker/volumes/db/data

echo "=== [4/8] Exporting DB dump from old EC2 ==="
# Dump via pg_dump through the supabase-db container on the OLD box
ssh ubuntu@${OLD_IP} "cd /home/ubuntu/supabase && sudo docker compose -f docker/docker-compose.yml exec -T supabase-db pg_dump -U postgres -Fc postgres" > /tmp/supabase.dump
ls -lh /tmp/supabase.dump

echo "=== [5/8] Starting supabase stack (fresh db, then restore) ==="
cd /home/ubuntu/supabase
sudo docker compose -f docker/docker-compose.yml up -d --remove-orphans 2>/dev/null || \
sudo docker-compose -f docker/docker-compose.yml up -d --remove-orphans
echo "Waiting for DB to be ready..."
for i in $(seq 1 60); do
  if sudo docker exec supabase-db pg_isready -U postgres >/dev/null 2>&1; then echo "DB ready"; break; fi
  sleep 2
done

echo "=== [6/8] Restoring dump ==="
sudo docker exec -i supabase-db pg_restore -U postgres -d postgres --clean --if-exists < /tmp/supabase.dump || echo "WARN: pg_restore partial (some objects may already exist)"

echo "=== [7/8] Starting Rallly ==="
cd /home/ubuntu/rallly
sudo docker compose up -d --remove-orphans 2>/dev/null || sudo docker-compose up -d --remove-orphans

echo "=== [8/8] Verifying ==="
echo "--- Containers ---"
sudo docker ps --format '{{.Names}} {{.Status}}'
echo "--- Supabase health ---"
curl -sf http://localhost:8000/rest/v1/ 2>/dev/null | head -1 || echo "rest check later (kong port may differ)"
echo "--- Rallly ---"
curl -sf http://localhost:3001 2>/dev/null | head -1 || echo "rallly check later"

echo "=== MIGRATION DONE. Next: point backend to this instance. ==="
