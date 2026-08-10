#!/bin/bash
# Run import on EC2 (reads export dir, pushes through gateway)
cd /home/ubuntu/sba-backend
export KEY=$(grep -E '^SUPABASE_SERVICE_KEY=' /home/ubuntu/sba-backend/.env | sed 's/^SUPABASE_SERVICE_KEY=//' | tr -d '\r\n')
/home/ubuntu/sba-backend/venv/bin/python /home/ubuntu/sba-backend/_pb_import.py /home/ubuntu/pb_export http://127.0.0.1:8095 "$KEY"
