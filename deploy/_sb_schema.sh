#!/bin/bash
echo "=== leads schema ==="
docker exec supabase-db psql -U postgres -d postgres -c "\d public.leads" 2>&1 | head -40
echo ""
echo "=== tables in public schema ==="
docker exec supabase-db psql -U postgres -d postgres -c "\dt public.*" 2>&1 | head -40
echo ""
echo "=== workspace schemas ==="
docker exec supabase-db psql -U postgres -d postgres -c "select schema_name from information_schema.schemata where schema_name like 'ws\_%' order by 1;" 2>&1 | head -20
