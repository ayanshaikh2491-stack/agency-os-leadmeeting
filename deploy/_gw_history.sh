#!/bin/bash
# Check what import artifacts exist on EC2 + when the 500s happened
echo "=== import-related files ==="
ls -la /home/ubuntu/*.py 2>/dev/null | grep -iE 'import|pb|gw' 
ls -la /home/ubuntu/sba-backend/_pb_import.py /home/ubuntu/_pb_import.py 2>&1
echo "=== pb_import logs anywhere ==="
find /home/ubuntu -maxdepth 2 -name '*import*' -newermt '2026-08-08' 2>/dev/null
echo "=== gw log line count + first 500 line number ==="
wc -l /home/ubuntu/sba-backend/pb_gw.log
grep -n "500" /home/ubuntu/sba-backend/pb_gw.log | head -3
grep -n "500" /home/ubuntu/sba-backend/pb_gw.log | tail -3
echo "=== gw log last modified ==="
ls -la /home/ubuntu/sba-backend/pb_gw.log
echo "=== count non-500 success lines in gw log ==="
grep -cE " (201|200) " /home/ubuntu/sba-backend/pb_gw.log
echo "=== env SUPABASE_URL in backend ==="
grep -E '^SUPABASE_URL=' /home/ubuntu/sba-backend/.env
grep -E '^SUPABASE_SERVICE_KEY=' /home/ubuntu/sba-backend/.env | sed 's/=.*/=<redacted>/'
