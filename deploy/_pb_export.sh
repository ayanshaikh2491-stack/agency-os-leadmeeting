#!/bin/bash
# Export all user tables as JSONL to files (backup + import source)
OUT=/home/ubuntu/pb_export
mkdir -p $OUT
cd $OUT

export_tbl() {
  local schema=$1 table=$2
  local fname="${schema}__${table}.jsonl"
  sudo docker exec supabase-db psql -U postgres -d postgres -t -A -c \
    "SELECT row_to_json(t) FROM ${schema}.${table} t;" 2>/dev/null > $fname
  local lines=$(wc -l < $fname)
  echo "${schema}.${table}: ${lines} rows -> $fname"
}

# public tables (skip huge/irrelevant? import all)
for t in agent_budget_logs agents client_users clients execution_logs goals heartbeat_log leads org_charts ticket_messages tickets users website_build_log website_builds website_docs workspaces; do
  export_tbl public $t
done

# ws_agency + ws_default
for s in ws_agency ws_default; do
  for t in agent_checkpoint_writes agent_checkpoints agent_data agent_memory agent_messages clients leads website_build_log website_builds website_docs; do
    export_tbl $s $t
  done
done

echo "=== TOTAL SIZE ==="
du -sh $OUT
