#!/bin/bash
echo "=== CEO error traceback in sba.service logs ==="
journalctl -u sba.service -n 400 --no-pager 2>/dev/null | grep -A 30 "CEO LangGraph execution failed" | tail -40
echo "=== any recent exception ==="
journalctl -u sba.service -n 200 --no-pager 2>/dev/null | grep -B2 -A 20 "Exception\|Traceback" | tail -50
echo "=== openai key present? ==="
grep -c "OPENAI" /home/ubuntu/sba-backend/.env 2>/dev/null
grep -E "OPENAI_API_KEY|GROQ" /home/ubuntu/sba-backend/.env 2>/dev/null | sed 's/=\(.\{8\}\).*/=\1***/' | head -5
