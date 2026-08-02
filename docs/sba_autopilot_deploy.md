# SBA 24/7 Autopilot — Deploy Notes

1. Copy repo to server: `/home/ubuntu/sba-backend` (existing).
2. Ensure `.env` has:
   - `SBA_OWNER_EMAIL` + `SBA_OWNER_EMAIL_PASSWORD` (Gmail App Password)
   - `SBA_OWNER_TIMEZONE=Asia/Kolkata`
   - `SBA_AUTOPILOT_INTERVAL_MINUTES=15`
   - `SBA_DAILY_EMAIL_CAP=30`
   - `WORKSPACE_API_KEY/BASE/MODEL` (LLM for email drafting)
   - `SUPABASE_URL` + `SUPABASE_SERVICE_KEY`
3. Install: `pip install tzdata`
4. Enable + start:
   ```bash
   sudo cp deploy/sba-autopilot.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now sba-autopilot
   ```
5. Verify:
   ```bash
   sudo systemctl status sba-autopilot
   journalctl -u sba-autopilot -f   # heartbeat + pass stats
   ```
6. Status API: `GET /api/sba/autopilot/status`

Behavior: loop kabhi soye nahi. Emails sirf lead ke local business hours mein
jaate hain. Worker (`admin/agency/worker.py`) remove kar diya gaya — SBA agent
khud sab karta hai.
