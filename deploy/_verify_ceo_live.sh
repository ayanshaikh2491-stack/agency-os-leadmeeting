#!/bin/bash
echo "===1 ceo.py get_checkpointer==="
grep -c "get_checkpointer" /home/ubuntu/sba-backend/admin/agency/ceo.py
echo "===2 routes/ceo.py conversation_id==="
grep -c "conversation_id" /home/ubuntu/sba-backend/admin/api/routes/ceo.py
echo "===3 live chat test==="
curl -s -X POST http://localhost:8000/api/ceo/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Bhai, 1 line mein status batao", "conversation_id":"deploy-test-1"}' \
  -m 60 || echo "CHAT_FAILED"
echo ""
echo "===4 health==="
curl -s http://localhost:8000/api/health -m 10
echo ""
echo "===5 journal autopilot tail==="
journalctl -u sba-autopilot.service -n 3 --no-pager 2>/dev/null | tail -3
