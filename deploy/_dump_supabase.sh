#!/bin/bash
# Dump Supabase DB for backup + migration (both formats)
cd /home/ubuntu/supabase 2>/dev/null || { echo "no supabase dir"; exit 1; }
TS=$(date +%Y%m%d_%H%M%S)
echo "=== CUSTOM FORMAT DUMP ==="
sudo docker compose -f docker/docker-compose.yml exec -T supabase-db pg_dump -U postgres -Fc postgres > /home/ubuntu/supabase_backup_${TS}.dump
ls -lh /home/ubuntu/supabase_backup_${TS}.dump
echo "=== PLAIN SQL DUMP (data only, with inserts) ==="
sudo docker compose -f docker/docker-compose.yml exec -T supabase-db pg_dump -U postgres --data-only --inserts --column-inserts postgres > /home/ubuntu/supabase_backup_${TS}.sql
ls -lh /home/ubuntu/supabase_backup_${TS}.sql
echo "=== TABLE LIST ==="
sudo docker compose -f docker/docker-compose.yml exec -T supabase-db psql -U postgres -d postgres -c "\dt *.*" 2>/dev/null | grep -vE '^$|pg_catalog|information_schema|pgsodium|vault|supabase_|auth\.|storage\.|realtime\.|extensions\.' | head -40
echo "=== SCHEMAS ==="
sudo docker compose -f docker/docker-compose.yml exec -T supabase-db psql -U postgres -d postgres -c "\dn" 2>/dev/null | head -20
echo "=== ROW COUNTS (key tables) ==="
sudo docker compose -f docker/docker-compose.yml exec -T supabase-db psql -U postgres -d postgres -t -c "SELECT 'public.leads', count(*) FROM public.leads UNION ALL SELECT 'public.meetings', count(*) FROM public.meetings;" 2>/dev/null
echo "=== WS SCHEMA TABLES ==="
sudo docker compose -f docker/docker-compose.yml exec -T supabase-db psql -U postgres -d postgres -c "\dt ws_agency.*" 2>/dev/null | head -20
