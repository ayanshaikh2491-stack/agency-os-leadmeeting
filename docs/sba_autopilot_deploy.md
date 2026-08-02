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

## Meeting Translation + Notes (speech-to-speech)

Meeting ke time live speech-to-speech translation + notes ke liye:

- Page: `GET /api/sba/meetings/translate-page` (phone/laptop pe kholo)
- Speech → translated text + audio: `POST /api/sba/meetings/audio/translate`
- Full meeting (transcribe + translate + summary + notes):
  `POST /api/sba/meetings/process` (multipart `audio` + optional `meeting_id`)
- Text → speech: `POST /api/sba/meetings/tts`

TTS provider (env `SBA_TTS_PROVIDER`):
- `belt` — inference.sh CLI (`belt app run inworld/text-to-speech-2`), best quality,
  `SBA_TTS_VOICE` (default `Sarah`). Install: `curl -fsSL https://raw.githubusercontent.com/inference-sh/skills/refs/heads/main/cli-install.md | sh` then `belt login`.
- `openai` — OpenAI-compatible `/v1/audio/speech` via WORKSPACE keys,
  `SBA_TTS_MODEL` (default `tts-1`), `SBA_TTS_VOICE` (default `alloy`).
- `mock` (default) — silent WAV, safe offline; real speech ke liye `belt` ya `openai` set karo.

Notes folder: `SBA_MEETING_NOTES_DIR` (default `data/meetings/`). Meeting record
mein bhi notes save hote hain jab `meeting_id` pass karo.
