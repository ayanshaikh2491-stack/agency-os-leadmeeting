#!/bin/bash
echo "=== LAST 60 lines sba.service ==="
journalctl -u sba.service -n 60 --no-pager 2>/dev/null | tail -60
echo "=== .env LLM keys (masked) ==="
grep -iE "OPENAI|GROQ|LLM|API_KEY|MODEL" /home/ubuntu/sba-backend/.env 2>/dev/null | sed -E 's/=([A-Za-z0-9_-]{6}).*/=\1***/' | head -12
echo "=== settings.py default llm ==="
grep -iE "openai|groq|api_key|model" /home/ubuntu/sba-backend/admin/config/settings.py | head -20
