# admin/tests/test_sba_autopilot.py
import pytest

from admin.agency.sba_autopilot import SBAAutopilot, _is_valid_lead_email


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

    lead = {"id": "10", "name": "Al's Auto", "email": "al@alsauto.com",
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
    assert email.sent[0]["to"] == "al@alsauto.com"


@pytest.mark.asyncio
async def test_run_once_skips_email_outside_business_hours(monkeypatch):
    email = FakeEmailClient()
    ap = SBAAutopilot(email_client=email)
    lead = {"id": "11", "name": "Night Biz", "email": "night@nightbiz.com",
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

    lead = {"id": "12", "name": "Lead Co", "email": "lead@leadco.com",
            "category": "cleaning", "state": "TX", "status": "contacted"}
    owner_reply = {"from_addr": "boss@ownerco.com", "subject": "Re: lead 12", "body_preview": "Haan 3 baje"}

    monkeypatch.setattr("admin.agency.sba_autopilot.load_leads", lambda u, k: [lead])
    monkeypatch.setattr("admin.agency.sba_autopilot.supabase_config", lambda: ("http://x", "key"))
    monkeypatch.setattr("admin.agency.sba_autopilot.sb_patch_lead", lambda u, k, sid, upd: True)
    monkeypatch.setattr("admin.agency.sba_autopilot.is_owner", lambda a: True)
    monkeypatch.setattr("admin.agency.sba_autopilot.parse_owner_command", lambda s, b: {"lead_id": "12", "action": "haan", "time": "15:00"})
    email.replies = [owner_reply]

    stats = await ap.run_once()
    assert stats["meetings_scheduled"] == 1
    assert mm.created and mm.created[0]["lead_id"] == "12"


def test_email_validity_filter():
    # Real-looking business emails pass
    assert _is_valid_lead_email("al@alsauto.com") is True
    assert _is_valid_lead_email("victor@quixana.com") is True
    # Junk domains / generic catch-alls / malformed get blocked
    assert _is_valid_lead_email("support@discord.com") is False
    assert _is_valid_lead_email("admission@denison.edu") is False
    assert _is_valid_lead_email("info@visitdallas.com") is False
    assert _is_valid_lead_email("contact@gbg.com") is False
    assert _is_valid_lead_email("blaisefromparis@gmail.com") is False
    assert _is_valid_lead_email("u003eaccountrecovery@deviantart.com") is False
    assert _is_valid_lead_email("not-an-email") is False
    assert _is_valid_lead_email("test@example.com") is False
    assert _is_valid_lead_email("") is False
    # HTML/JS-escape leftovers in the local part are mangled fragments
    assert _is_valid_lead_email("u003epetmd@wrightsmedia.com") is False
    assert _is_valid_lead_email("%3eowner@realbiz.com") is False
    assert _is_valid_lead_email("hello%26gt;x@realbiz.com") is False


class FailingEmailClient:
    """Always fails so we can exercise the SMTP attempt cap + backoff."""

    def __init__(self):
        self.enabled = True
        self.sent = []
        self.replies = []

    async def send_email(self, to_email, subject, body_text, cc_owner=True):
        self.sent.append({"to": to_email})
        return False

    async def check_replies(self, mark_read=True):
        return self.replies


def _business_hours(monkeypatch):
    import datetime as dt

    monkeypatch.setattr(
        "admin.tools.sba_time.now_in",
        lambda tz: dt.datetime(2026, 8, 3, 17, 0, tzinfo=dt.timezone.utc).astimezone(
            __import__("admin.tools.sba_time", fromlist=["load_zone"]).load_zone("America/Chicago")
        ),
    )


def _no_new_leads(monkeypatch):
    monkeypatch.setattr(
        "admin.tools.sba_lead_sources.find_leads_all", lambda *a, **k: []
    )


@pytest.mark.asyncio
async def test_run_once_caps_smtp_attempts_on_failure(monkeypatch):
    """Failed sends count toward the cap so one pass can't burn Gmail's limit."""
    import admin.agency.sba_autopilot as mod

    monkeypatch.setattr(mod, "DAILY_EMAIL_CAP", 2)
    email = FailingEmailClient()
    ap = mod.SBAAutopilot(email_client=email)
    leads = [
        {"id": str(i), "name": f"Biz {i}", "email": f"owner{i}@biz{i}.com",
         "category": "plumber", "state": "TX", "status": "new"}
        for i in range(5)
    ]
    monkeypatch.setattr(mod, "load_leads", lambda u, k: leads)
    monkeypatch.setattr(mod, "supabase_config", lambda: ("http://x", "key"))
    monkeypatch.setattr(mod, "sb_patch_lead", lambda u, k, sid, upd: True)
    _business_hours(monkeypatch)
    _no_new_leads(monkeypatch)

    stats = await ap.run_once()
    assert stats["send_failed"] == 2
    assert len(email.sent) == 2  # cap respected: only 2 SMTP attempts


@pytest.mark.asyncio
async def test_run_once_backs_off_failed_recipients(monkeypatch):
    """A failed recipient is not re-hammered on the next pass."""
    import admin.agency.sba_autopilot as mod

    monkeypatch.setattr(mod, "DAILY_EMAIL_CAP", 10)
    email = FailingEmailClient()
    ap = mod.SBAAutopilot(email_client=email)
    lead = {"id": "1", "name": "Slow Co", "email": "slow@slowco.com",
            "category": "hvac", "state": "TX", "status": "new"}
    monkeypatch.setattr(mod, "load_leads", lambda u, k: [lead])
    monkeypatch.setattr(mod, "supabase_config", lambda: ("http://x", "key"))
    monkeypatch.setattr(mod, "sb_patch_lead", lambda u, k, sid, upd: True)
    _business_hours(monkeypatch)
    _no_new_leads(monkeypatch)

    s1 = await ap.run_once()
    assert s1["send_failed"] == 1
    s2 = await ap.run_once()
    assert s2["send_failed"] == 0
    assert s2["retry_backoff"] == 1
    assert len(email.sent) == 1  # no second attempt while in backoff
