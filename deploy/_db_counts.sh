#!/bin/bash
echo "=== PUBLIC ROW COUNTS ==="
sudo docker exec supabase-db psql -U postgres -d postgres -t -c "
SELECT 'public.'||tablename, n_live_tup FROM pg_stat_user_tables
WHERE schemaname='public' ORDER BY tablename;" 2>/dev/null
echo "=== WS ROW COUNTS ==="
sudo docker exec supabase-db psql -U postgres -d postgres -t -c "
SELECT schemaname||'.'||tablename, n_live_tup FROM pg_stat_user_tables
WHERE schemaname LIKE 'ws\_%' ORDER BY schemaname, tablename;" 2>/dev/null
echo "=== LEADS SCHEMA ==="
sudo docker exec supabase-db psql -U postgres -d postgres -c "\d public.leads" 2>/dev/null | head -40
echo "=== AGENT_MEMORY SCHEMA ==="
sudo docker exec supabase-db psql -U postgres -d postgres -c "\d ws_agency.agent_memory" 2>/dev/null | head -25
