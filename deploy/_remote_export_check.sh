#!/bin/bash
# Remote: check export data + import status
set +e
echo "=== export dir contents ==="
ls -la /home/ubuntu/pb_export/ 2>/dev/null | head -30
echo "--- sizes ---"
du -sh /home/ubuntu/pb_export/* 2>/dev/null | head -30

echo ""
echo "=== import log / history ==="
ls -la /home/ubuntu/sba-backend/_pb_import*.log /tmp/pb_import*.log 2>/dev/null
grep -rn 'imported\|done\|rows' /home/ubuntu/sba-backend/pb_import.log 2>/dev/null | tail -10

echo ""
echo "=== what tables exist in export? ==="
for f in /home/ubuntu/pb_export/*.jsonl; do
  [ -f "$f" ] && echo "$(basename $f): $(wc -l < $f) rows"
done 2>/dev/null
