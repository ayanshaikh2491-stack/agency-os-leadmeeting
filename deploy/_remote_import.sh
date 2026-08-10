#!/bin/bash
# Remote: run full import Supabase exports -> PocketBase via gateway
set +e
cd /home/ubuntu/sba-backend
SRVKEY=$(grep -E '^SUPABASE_SERVICE_KEY=' /home/ubuntu/sba-backend/.env | sed 's/^SUPABASE_SERVICE_KEY=//' | tr -d '\r\n')
echo "KEYLEN=${#SRVKEY}"
time venv/bin/python _pb_import.py /home/ubuntu/pb_export http://127.0.0.1:8095 "$SRVKEY" 2>&1 | tail -60
