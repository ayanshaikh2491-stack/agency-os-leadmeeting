"""Test all SBA endpoints one by one."""
import json
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:9002/api/sba"

def api(method, path, body=None):
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"ERROR": e.code, "body": json.loads(e.read())}
    except Exception as e:
        return {"ERROR": str(e)}

def p(label, data):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    print(json.dumps(data, indent=2, default=str))

# ── 1. STATUS ──────────────────────────────────────
p("1️⃣  GET /api/sba/status", api("GET", "/status"))

# ── 2. CREATE LEAD ──────────────────────────────────
lead = api("POST", "/leads", {
    "name": "Rahul Sharma",
    "business_name": "Sharma Tech Solutions",
    "email": "rahul@sharmatech.com",
    "phone": "+91-9876543210",
    "source": "linkedin",
    "score": 85,
    "context": {
        "needs": ["SEO", "Website redesign"],
        "estimated_value": 50000,
        "key_signals": "Founder looking to scale digital presence"
    }
})
p("2️⃣  POST /api/sba/leads (create)", lead)
lead_id = lead.get("data", {}).get("lead", {}).get("id", "NO-ID")

# ── 3. LIST LEADS ───────────────────────────────────
p("3️⃣  GET /api/sba/leads", api("GET", "/leads"))

# ── 4. GET LEAD ─────────────────────────────────────
if lead_id != "NO-ID":
    p("4️⃣  GET /api/sba/leads/{id}", api("GET", f"/leads/{lead_id}"))

# ── 5. UPDATE LEAD ──────────────────────────────────
if lead_id != "NO-ID":
    p("5️⃣  PATCH /api/sba/leads/{id} (status→contacted)", 
      api("PATCH", f"/leads/{lead_id}", {"status": "contacted", "score": 90}))

# ── 6. PIPELINE ─────────────────────────────────────
p("6️⃣  GET /api/sba/pipeline", api("GET", "/pipeline"))

# ── 7. CREATE MEETING ───────────────────────────────
if lead_id != "NO-ID":
    meeting = api("POST", "/meetings", {
        "lead_id": lead_id,
        "title": "Discovery Call",
        "date": "2026-07-15",
        "time": "14:00",
        "duration_minutes": 45
    })
    p("7️⃣  POST /api/sba/meetings", meeting)
    meeting_id = meeting.get("data", {}).get("meeting", {}).get("id", "NO-ID")
else:
    meeting_id = "NO-ID"

# ── 8. LIST MEETINGS ────────────────────────────────
p("8️⃣  GET /api/sba/meetings", api("GET", "/meetings"))

# ── 9. GET MEETING ──────────────────────────────────
if meeting_id != "NO-ID":
    p("9️⃣  GET /api/sba/meetings/{id}", api("GET", f"/meetings/{meeting_id}"))

# ── 10. ADD MEETING NOTE (Hinglish!) ────────────────
if meeting_id != "NO-ID":
    p("🔟  POST /api/sba/meetings/{id}/notes (Hinglish)", 
      api("POST", f"/meetings/{meeting_id}/notes", {
          "text": "Client ne kaha ki SEO pe focus karna hai, budget 50k hai, haan bola final deal ke liye",
          "language": "hi",
          "speaker": "lead"
      }))
    
    # Second note
    api("POST", f"/meetings/{meeting_id}/notes", {
        "text": "Rahul seems genuinely interested. Follow up with proposal by Friday.",
        "language": "en",
        "speaker": "me"
    })

# ── 11. UPDATE MEETING ──────────────────────────────
if meeting_id != "NO-ID":
    p("1️⃣1️⃣  PATCH /api/sba/meetings/{id} (lead_response→haan)",
      api("PATCH", f"/meetings/{meeting_id}", {
          "summary": "Client agreed to move forward",
          "lead_response": "haan",
          "status": "done"
      }))

# ── 12. UPDATE LEAD TO CLOSING STAGE ────────────────
if lead_id != "NO-ID":
    p("1️⃣2️⃣  PATCH /api/sba/leads/{id} (status→closed)",
      api("PATCH", f"/leads/{lead_id}", {"status": "meeting"}))

# ── 13. HANDS-OFF! (SBA → CEO) ──────────────────────
if lead_id != "NO-ID":
    p("1️⃣3️⃣  POST /api/sba/leads/{id}/handoff",
      api("POST", f"/leads/{lead_id}/handoff", {
          "ceo_message": "Rahul Sharma ready hai! SEO + Website redesign chahiye, budget 50k confirmed."
      }))

# ── 14. LIST HANDOFFS ───────────────────────────────
p("1️⃣4️⃣  GET /api/sba/handoffs", api("GET", "/handoffs"))

# ── 15. FINANCE ─────────────────────────────────────
p("1️⃣5️⃣  GET /api/sba/finance", api("GET", "/finance"))

# ── 16. LEAD QUALIFY ────────────────────────────────
p("1️⃣6️⃣  POST /api/sba/leads/qualify",
  api("POST", "/leads/qualify", {
      "lead": {
          "name": "Priya Patel",
          "business_name": "Patel Enterprises",
          "email": "priya@patelent.com",
          "source": "upwork",
          "score": 60
      }
  }))

print("\n\n🎯 ALL ENDPOINTS TESTED!")
