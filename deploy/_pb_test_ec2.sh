#!/bin/bash
# Run gateway test suite on EC2 against local gateway (8095)
cd /home/ubuntu/sba-backend
export GW_BASE="http://127.0.0.1:8095"
export GW_KEY=$(grep -E '^SUPABASE_SERVICE_KEY=' /home/ubuntu/sba-backend/.env | sed 's/^SUPABASE_SERVICE_KEY=//' | tr -d '\r\n')
/home/ubuntu/sba-backend/venv/bin/python /home/ubuntu/sba-backend/_pb_gw_test.py
