# admin/tests/test_sba_autopilot.py
import pytest

from admin.agency.sba_autopilot import SBAAutopilot


class FakeEmailClient:
    def __init__(self):
        self.enabled = True
        self.sent = []
        self.replies = []

    async def send_email(self, to_email, subject, body_text, cc_owner=True):
        self.sent.append({"to": to_email, "subject": subject})
        return True

    async def check_replies(self, mark_read=True):
        return self.replies


class FakeMeetingManager:
    def __init__(self):
        self.created = []

    async def create_meeting(self, lead_id, lead_name, lead_email, proposed_time, duration_minutes=30):
        rec = {"lead_id": lead_id, "lead_name": lead_name, "time": proposed_time}
        self.created.append(rec)
        return rec


@pytest.mark.asyncio
async def test_run_once_sends_email_to_lead_in_business_hours(monkeypatch):
    email = FakeEmailClient()
    mm = FakeMeetingManager()
    ap = SBAAutopilot(email_client=email, meeting_manager=mm)

    lead = {"id": "10", "name": "Al's Auto", "email": "al@example.com",
            "category": "auto repair", "state": "TX", "status": "new",
            "city_state": "Houston, TX"}
    monkeypatch.setattr("admin.agency.sba_autopilot.load_leads", lambda u, k: [lead])
    monkeypatch.setattr("admin.agency.sba_autopilot.supabase_config", lambda: ("http://x", "key"))
    monkeypatch.setattr("admin.agency.sba_autopilot.sb_patch_lead", lambda u, k, sid, upd: True)

    # Force business hours: 17:00 UTC = 12:00 CDT (America/Chicago, Mon)
    import datetime as dt
    monkeypatch.setattr(
        "admin.tools.sba_time.now_in",
        lambda tz: dt.datetime(2026, 8, 3, 17, 0, tzinfo=dt.timezone.utc).astimezone(
            __import__("admin.tools.sba_time", fromlist=["load_zone"]).load_zone("America/Chicago")
        ),
    )

    stats = await ap.run_once()
    assert stats["emails_sent"] == 1
    assert email.sent[0]["to"] == "al@example.com"


@pytest.mark.asyncio
async def test_run_once_skips_email_outside_business_hours(monkeypatch):
    email = FakeEmailClient()
    ap = SBAAutopilot(email_client=email)
    lead = {"id": "11", "name": "Night Biz", "email": "night@example.com",
            "category": "bar", "state": "CA", "status": "new"}
    monkeypatch.setattr("admin.agency.sba_autopilot.load_leads", lambda u, k: [lead])
    monkeypatch.setattr("admin.agency.sba_autopilot.supabase_config", lambda: ("http://x", "key"))

    # Night in LA: 06:00 UTC on 8/4 = 23:00 PDT on 8/3 (Mon) -> outside 9-17
    import datetime as dt
    monkeypatch.setattr(
        "admin.tools.sba_time.now_in",
        lambda tz: dt.datetime(2026, 8, 4, 6, 0, tzinfo=dt.timezone.utc).astimezone(
            __import__("admin.tools.sba_time", fromlist=["load_zone"]).load_zone("America/Los_Angeles")
        ),
    )

    stats = await ap.run_once()
    assert stats["emails_sent"] == 0
    assert email.sent == []
    assert stats["deferred_to_business_hours"] == 1


@pytest.mark.asyncio
async def test_run_once_schedules_meeting_on_owner_confirm(monkeypatch):
    email = FakeEmailClient()
    mm = FakeMeetingManager()
    ap = SBAAutopilot(email_client=email, meeting_manager=mm)

    lead = {"id": "12", "name": "Lead Co", "email": "lead@example.com",
            "category": "cleaning", "state": "TX", "status": "contacted"}
    owner_reply = {"from_addr": "boss@example.com", "subject": "Re: lead 12", "body_preview": "Haan 3 baje"}

    monkeypatch.setattr("admin.agency.sba_autopilot.load_leads", lambda u, k: [lead])
    monkeypatch.setattr("admin.agency.sba_autopilot.supabase_config", lambda: ("http://x", "key"))
    monkeypatch.setattr("admin.agency.sba_autopilot.sb_patch_lead", lambda u, k, sid, upd: True)
    monkeypatch.setattr("admin.agency.sba_autopilot.is_owner", lambda a: True)
    monkeypatch.setattr("admin.agency.sba_autopilot.parse_owner_command", lambda s, b: {"lead_id": "12", "action": "haan", "time": "15:00"})
    email.replies = [owner_reply]

    stats = await ap.run_once()
    assert stats["meetings_scheduled"] == 1
    assert mm.created and mm.created[0]["lead_id"] == "12"
