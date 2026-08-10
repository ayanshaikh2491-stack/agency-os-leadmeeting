#!/bin/bash
TS=$(date +%Y%m%d_%H%M%S)
echo "=== DUMP (docker exec direct) ==="
sudo docker exec supabase-db pg_dump -U postgres -Fc postgres > /home/ubuntu/supabase_backup_${TS}.dump
ls -lh /home/ubuntu/supabase_backup_${TS}.dump
echo "=== SQL DUMP (data only) ==="
sudo docker exec supabase-db pg_dump -U postgres --data-only --inserts --column-inserts postgres > /home/ubuntu/supabase_backup_${TS}.sql
ls -lh /home/ubuntu/supabase_backup_${TS}.sql
echo "=== PUBLIC TABLES ==="
sudo docker exec supabase-db psql -U postgres -d postgres -c "\dt public.*" 2>/dev/null | head -30
echo "=== WS SCHEMAS ==="
sudo docker exec supabase-db psql -U postgres -d postgres -c "\dn" 2>/dev/null | head -20
echo "=== WS TABLES ==="
sudo docker exec supabase-db psql -U postgres -d postgres -c "\dt ws_*.*" 2>/dev/null | head -40
echo "=== ROW COUNTS ==="
sudo docker exec supabase-db psql -U postgres -d postgres -t -c "SELECT 'public.leads', count(*) FROM public.leads UNION ALL SELECT 'public.meetings', count(*) FROM public.meetings;" 2>/dev/null
echo "=== SERVICE KEY VALUE (first 12 chars) ==="
grep -E '^SUPABASE_SERVICE_KEY=' /home/ubuntu/sba-backend/.env | sed 's/SUPABASE_SERVICE_KEY=//' | cut -c1-12
echo "=== SERVICE KEY LENGTH ==="
grep -E '^SUPABASE_SERVICE_KEY=' /home/ubuntu/sba-backend/.env | sed 's/SUPABASE_SERVICE_KEY=//' | tr -d '\n' | wc -c
