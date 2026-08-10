#!/bin/bash
echo "=== BACKEND DIR ==="
ls -la /home/ubuntu/sba-backend/ 2>/dev/null | head -20
echo ""
echo "=== .env SUPABASE REFS ==="
grep -iE 'supabase|pocketbase|8050|8090|REST|API_URL|DATABASE|OPENAI|GROQ|ANTHROPIC' /home/ubuntu/sba-backend/.env 2>/dev/null | sed 's/=.*/=<redacted>/' 
echo ""
echo "=== FULL .env KEYS ONLY ==="
cut -d= -f1 /home/ubuntu/sba-backend/.env 2>/dev/null
echo ""
echo "=== HOW BACKEND RUNS (systemd/pm2/screen) ==="
ps aux | grep -iE 'uvicorn|gunicorn|fastapi|api.py|main.py|autopilot' | grep -v grep | head -10
echo ""
echo "=== SYSTEMD UNITS ==="
systemctl list-units --type=service --state=running 2>/dev/null | grep -iE 'sba|backend|api|agency' | head
echo ""
echo "=== BACKEND PORT ==="
ss -tlnp 2>/dev/null | grep -E ':(8000|8050|8090|3000|3001)\b' | head
echo ""
echo "=== PYTHON VENV ==="
ls -d /home/ubuntu/sba-backend/venv 2>/dev/null || ls -d /home/ubuntu/*venv* 2>/dev/null || echo "no venv found"
