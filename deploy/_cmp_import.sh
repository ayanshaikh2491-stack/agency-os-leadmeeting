#!/bin/bash
echo "=== EC2 import script md5 vs content ==="
md5sum /home/ubuntu/sba-backend/_pb_import.py
echo "--- key lines ---"
grep -n "legacy\|pop\|id" /home/ubuntu/sba-backend/_pb_import.py | head -30
echo "=== local import script md5 ==="
