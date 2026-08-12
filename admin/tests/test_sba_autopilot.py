# admin/tests/test_sba_autopilot.py
import pytest

from admin.agency.sba_autopilot import SBAAutopilot, _is_valid_lead_email


@pytest.fixture(autouse=True)
def _no_real_llm(monkeypatch):
    """Keep the reasoning layer deterministic: the LLM email second-opinion
    always approves, as if the model agreed the mailbox belongs to the business.
    (The reasoning layer itself has its own tests in test_sba_reason.py.)"""
    async def _ok(*args, **kwargs):
        return {"ok": True, "confidence": 1.0, "reason": "test"}
    monkeypatch.setattr("admin.agency.sba_reason.verify_email", _ok)


@pytest.fixture(autouse=True)
def _isolate_enrich_state(monkeypatch, tmp_path):
    """Each test gets a fresh persisted enrichment-retry state so the 24h
    cooldown never leaks across tests (or into the repo's real state file)."""
    import admin.agency.sba_autopilot as mod
    monkeypatch.setattr(mod, "_ENRICH_STATE_FILE", str(tmp_path / "enrich_state.json"))


@pytest.fixture(autouse=True)
def _no_strategy_llm(monkeypatch, tmp_path):
    """Keep the post-pass strategy review deterministic: it must never call the
    real LLM or write the repo's real strategy/journal state files."""
    async def _noop_review(*args, **kwargs):
        return None
    monkeypatch.setattr("admin.agency.sba_autopilot.strat.maybe_review", _noop_review)
    monkeypatch.setattr("admin.agency.sba_autopilot.strat.load_strategy", lambda path=None: {"angle": None, "focus": [], "notes": [], "actions": []})
    monkeypatch.setattr("admin.agency.sba_autopilot.strat.metrics_from_journal", lambda hours=None, log_path=None: {"passes": 0})
    monkeypatch.setattr("admin.agency.sba_autopilot.strat.observe_pass", lambda stats, path=None: {})


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
    _no_new_leads(monkeypatch)

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
    _no_new_leads(monkeypatch)

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
async def test_run_once_auto_books_meeting_on_lead_yes(monkeypatch):
    """A lead reply "yes" books the meeting automatically - no owner round-trip."""
    email = FakeEmailClient()
    mm = FakeMeetingManager()
    ap = SBAAutopilot(email_client=email, meeting_manager=mm)

    lead = {"id": "13", "name": "Green Lawn", "email": "lawn@greenlawn.com",
            "category": "landscaping", "state": "TX", "status": "contacted"}
    lead_reply = {"from_addr": "lawn@greenlawn.com", "subject": "Re: lawn",
                  "body_preview": "Yes, interested. 3 baje"}

    monkeypatch.setattr("admin.agency.sba_autopilot.load_leads", lambda u, k: [lead])
    monkeypatch.setattr("admin.agency.sba_autopilot.supabase_config", lambda: ("http://x", "key"))
    monkeypatch.setattr("admin.agency.sba_autopilot.sb_patch_lead", lambda u, k, sid, upd: True)
    monkeypatch.setattr(SBAAutopilot, "_is_owner", lambda self, a: False)

    async def _understand(text):
        return {"intent": "yes", "meeting_time": "15:00", "reason": "test"}
    monkeypatch.setattr("admin.agency.sba_reason.understand_reply", _understand)
    _no_new_leads(monkeypatch)
    email.replies = [lead_reply]

    stats = await ap.run_once()
    assert stats["meetings_scheduled"] == 1
    assert mm.created and mm.created[0]["lead_id"] == "13"
    assert mm.created[0]["time"]  # proposed slot was computed
    # Owner got a summary (no action needed), lead got the confirm via meeting manager.


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
    monkeypatch.setattr(SBAAutopilot, "_is_owner", lambda self, a: True)
    monkeypatch.setattr("admin.agency.sba_autopilot.parse_owner_command", lambda s, b: {"lead_id": "12", "action": "haan", "time": "15:00"})
    _no_new_leads(monkeypatch)
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
    # Wrong-domain emails seen in production: listing/media/visitor sites
    assert _is_valid_lead_email("bd@grubhub.com") is False
    assert _is_valid_lead_email("stories@wikihow.com") is False
    assert _is_valid_lead_email("info@midtownatl.com") is False
    assert _is_valid_lead_email("recreationdepartment@districtgov.org") is False
    assert _is_valid_lead_email("info@chamberofcommerce.com") is False
    # JS-bundle TLDs and gov/edu/mil are never a local business mailbox
    assert _is_valid_lead_email("preact@10.5.13.compat.module.min.js") is False
    assert _is_valid_lead_email("mail@nih.gov") is False
    assert _is_valid_lead_email("admissions@college.edu") is False
    assert _is_valid_lead_email("owner@localhost") is False
    # Generic first-party catch-all prefixes are not a decision maker
    assert _is_valid_lead_email("hello@realbiz.com") is False
    assert _is_valid_lead_email("stories@realdiner.com") is False
    assert _is_valid_lead_email("jane@realplumbing.com") is True
    # School domains + automated/aggregator local parts are not targets
    assert _is_valid_lead_email("mmcnulty@carrollschool.org") is False
    assert _is_valid_lead_email("ad-alerts@on4u.es") is False
    assert _is_valid_lead_email("notifications@realdiner.com") is False
    assert _is_valid_lead_email("webmaster@realdiner.com") is False


@pytest.mark.asyncio
async def test_run_once_enriches_candidate_without_email(monkeypatch):
    """A candidate lead with no email gets auto-enriched before the send gate."""
    import admin.agency.sba_autopilot as mod

    email = FakeEmailClient()
    ap = mod.SBAAutopilot(email_client=email)
    lead = {"id": "20", "name": "Fresh Plumbing Co", "email": "",
            "category": "plumber", "state": "TX", "status": "candidate",
            "city_state": "Austin, TX"}
    monkeypatch.setattr(mod, "load_leads", lambda u, k: [lead])
    monkeypatch.setattr(mod, "supabase_config", lambda: ("http://x", "key"))
    monkeypatch.setattr(mod, "sb_patch_lead", lambda u, k, sid, upd: True)
    async def fake_enrich(u, k, l):
        return "owner@freshplumbingco.com", "own_domain"
    monkeypatch.setattr(ap, "_enrich_lead_email", fake_enrich)
    _business_hours(monkeypatch)
    _no_new_leads(monkeypatch)

    stats = await ap.run_once()
    assert stats["emails_sent"] == 1
    assert email.sent[0]["to"] == "owner@freshplumbingco.com"


def test_enrichment_module_rejects_junk(monkeypatch):
    """The enrichment module uses the same strict validity as the autopilot."""
    from admin.tools.lead_enrichment import _is_valid_email, _name_tokens

    assert _is_valid_email("bd@grubhub.com") is False
    assert _is_valid_email("stories@wikihow.com") is False
    assert _is_valid_email("info@midtownatl.com") is False
    assert _is_valid_email("owner@freshplumbingco.com") is True
    # Business-name tokens drop filler words so homepage matching is precise
    assert "plumbing" not in _name_tokens("Cooper Plumbing & Air LLC")
    assert "cooper" in _name_tokens("Cooper Plumbing & Air LLC")


def test_homepage_gate_needs_phrase_for_short_names():
    """Short names with no distinctive tokens ("Paw Wow") must NOT let a random
    media page pass just because it mentions 'paw'/'wow' separately (the
    lgsupport@pluto.tv / paramountplus.com regression)."""
    from admin.tools.lead_enrichment import _name_phrase, _name_tokens, _text_matches_tokens

    tokens = _name_tokens("Paw Wow")
    phrase = _name_phrase("Paw Wow")
    assert tokens == []  # both words are too short to be distinctive
    assert phrase == "paw wow"

    # A streaming/media page mentioning the words separately must be rejected.
    media_title = "Paramount+ | Stream Movies, Series & Live TV | Paw Patrol, Sports & Wow"
    assert _text_matches_tokens(media_title, tokens, phrase) is False
    # The real grooming business's page (full name present) passes.
    real_title = "Paw Wow Grooming | Las Vegas Pet Spa"
    assert _text_matches_tokens(real_title, tokens, phrase) is True

    # 1 distinctive token: token alone is not enough, the full phrase is needed.
    coop_tokens = _name_tokens("Cooper Plumbing & Air LLC")
    assert coop_tokens == ["cooper"]
    coop_phrase = _name_phrase("Cooper Plumbing & Air LLC")
    assert coop_phrase == "cooper plumbing air"
    assert _text_matches_tokens("Cooper Plumbing & Air | Austin", coop_tokens, coop_phrase) is True
    # A page that only has the generic token (no full name) is rejected.
    assert _text_matches_tokens("Cooper Air Conditioning | Cooling Services", coop_tokens, coop_phrase) is False

    # 2+ distinctive tokens: ALL must appear (same-name other business fails).
    mid_tokens = _name_tokens("Midtown Smiles Dental")
    assert "midtown" in mid_tokens and "smiles" in mid_tokens
    assert _text_matches_tokens("Midtown Smiles Dental Care", mid_tokens, "") is True
    assert _text_matches_tokens("Midtown Comics & Gifts", mid_tokens, "") is False
    # No name at all -> never trust (no tokens AND no phrase).
    assert _text_matches_tokens("anything", [], "") is False


def test_rotation_cursor_survives_restart(monkeypatch, tmp_path):
    """The lead-rotation cursor persists so restarts don't re-scrape target #0."""
    import admin.agency.sba_autopilot as mod

    state = tmp_path / ".sba_rotation_state"
    import admin.agency.sba_biztypes as biztypes
    monkeypatch.setattr(biztypes, "rotation_state_path", lambda ws: str(state))
    ap1 = mod.SBAAutopilot()
    assert ap1._target_idx == 0
    ap1._target_idx += 1
    ap1._save_rotation_idx(ap1._target_idx)

    ap2 = mod.SBAAutopilot()  # simulate process restart
    assert ap2._target_idx == 1


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
    async def _no_leads(*a, **k):
        return []
    monkeypatch.setattr(
        "admin.tools.sba_lead_sources.find_leads_all", _no_leads
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


def test_consumer_email_requires_first_party_provenance():
    """A gmail address is junk unless enrichment proved it came from the
    business's own verified page (small local businesses run on gmail, so
    we must not block them entirely, but a random gmail is never a target)."""
    from admin.tools.lead_enrichment import _is_valid_email

    # Enrichment collect gate: gmail rejected by default...
    assert _is_valid_email("triangleroofingnola@gmail.com") is False
    # ...accepted from the business's own verified page.
    assert _is_valid_email("triangleroofingnola@gmail.com", allow_consumer=True) is True
    # Blocklist/prefix rules still apply even when consumer is allowed.
    assert _is_valid_email("you@company.com", allow_consumer=True) is False
    assert _is_valid_email("bd@grubhub.com", allow_consumer=True) is False
    assert _is_valid_email("investorrelations@wellsfargo.com", allow_consumer=True) is False
    assert _is_valid_email("info@gmail.com", allow_consumer=True) is False

    # Autopilot send gate: same rule, driven by email_provenance.
    assert _is_valid_lead_email("triangleroofingnola@gmail.com") is False
    assert _is_valid_lead_email("triangleroofingnola@gmail.com", allow_consumer=True) is True
    assert _is_valid_lead_email("you@company.com", allow_consumer=True) is False
    assert _is_valid_lead_email("bd@grubhub.com", allow_consumer=True) is False
    assert _is_valid_lead_email("investorrelations@wellsfargo.com", allow_consumer=True) is False
    assert _is_valid_lead_email("info@gmail.com", allow_consumer=True) is False


@pytest.mark.asyncio
async def test_consumer_email_from_verified_page_sends(monkeypatch):
    """End-to-end: a lead whose enrichment returned a gmail from its own
    verified page is emailed; the same gmail without provenance is skipped."""
    import admin.agency.sba_autopilot as mod

    monkeypatch.setattr(mod, "DAILY_EMAIL_CAP", 10)
    email = FakeEmailClient()
    ap = mod.SBAAutopilot(email_client=email)

    lead = {"id": "1", "name": "Triangle Roofing LLC", "email": "",
            "category": "roofer", "state": "LA", "status": "candidate",
            "city_state": "New Orleans, LA"}
    monkeypatch.setattr(mod, "load_leads", lambda u, k: [lead])
    monkeypatch.setattr(mod, "supabase_config", lambda: ("http://x", "key"))
    monkeypatch.setattr(mod, "sb_patch_lead", lambda u, k, sid, upd: True)

    # Enrichment returns a gmail mailbox found on the business's own page.
    async def fake_enrich(u, k, l):
        return "triangleroofingnola@gmail.com", "consumer"
    monkeypatch.setattr(ap, "_enrich_lead_email", fake_enrich)
    _business_hours(monkeypatch)
    _no_new_leads(monkeypatch)

    stats = await ap.run_once()
    assert stats["emails_sent"] == 1
    assert email.sent[0]["to"] == "triangleroofingnola@gmail.com"

    # Same address but enrichment could NOT prove first-party -> skipped.
    # Fresh instance + fresh lead id so the persisted 24h enrichment cooldown
    # (state file survives restarts now) doesn't skip the second run.
    email2 = FakeEmailClient()
    ap2 = mod.SBAAutopilot(email_client=email2)
    async def fake_enrich_junk(u, k, l):
        return "triangleroofingnola@gmail.com", ""
    monkeypatch.setattr(ap2, "_enrich_lead_email", fake_enrich_junk)
    lead["id"] = "2"  # different lead: cooldown keyed per lead id
    stats = await ap2.run_once()
    assert stats["emails_sent"] == 0
    assert stats["invalid_email"] == 1
    assert email2.sent == []
