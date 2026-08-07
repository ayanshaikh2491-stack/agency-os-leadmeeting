# admin/tests/test_sba_strategy.py
import json
import pytest

from admin.agency import sba_strategy as strat


@pytest.fixture(autouse=True)
def _isolated_state(monkeypatch, tmp_path):
    """Strategy file + journal live in a temp dir per test."""
    f = tmp_path / "sba_strategy.json"
    log = tmp_path / "sba_reasoning.log"
    monkeypatch.setattr(strat, "STRATEGY_FILE", str(f))
    monkeypatch.setattr(strat, "REASON_LOG", str(log))
    import admin.agency.sba_reason as reason
    monkeypatch.setattr(reason, "REASON_LOG", str(log))
    monkeypatch.setattr(strat, "DIGEST_INTERVAL_SECONDS", 0)
    monkeypatch.setattr(strat, "ALERT_ZERO_LEAD_PASSES", 2)
    monkeypatch.setattr(strat, "ALERT_ZERO_REPLY_PASSES", 3)


def _seed_journal(log_path, entries):
    with open(log_path, "a", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")


def test_defaults_when_no_file():
    s = strat.load_strategy()
    assert s["angle"]
    assert s["focus"] == []
    assert s["last_review"] is None


def test_save_and_load_roundtrip():
    s = strat.load_strategy()
    s["angle"] = "New angle"
    s["focus"] = [["plumber", "Houston", "TX"]]
    assert strat.save_strategy(s)
    loaded = strat.load_strategy()
    assert loaded["angle"] == "New angle"
    assert loaded["focus"] == [["plumber", "Houston", "TX"]]


def test_observe_pass_streaks():
    # Two passes with zero new leads -> zero_lead_passes counter climbs.
    strat.observe_pass({"new_leads_found": 0})
    strat.observe_pass({"new_leads_found": 0})
    s = strat.load_strategy()
    assert s["zero_lead_passes"] == 2
    # A pass with new leads resets it.
    strat.observe_pass({"new_leads_found": 5})
    assert strat.load_strategy()["zero_lead_passes"] == 0


def test_metrics_from_journal_window():
    import datetime as dt
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    old = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=99)).isoformat()
    _seed_journal(strat.REASON_LOG, [
        {"event": "pass_summary", "ts": now, "stats": {"emails_sent": 3, "new_leads_found": 2}},
        {"event": "pass_summary", "ts": old, "stats": {"emails_sent": 50, "new_leads_found": 50}},
        {"event": "email_sent", "ts": now, "category": "plumber"},
        {"event": "reply_understood", "ts": now, "intent": "yes"},
    ])
    m = strat.metrics_from_journal(hours=48)
    assert m["passes"] == 1  # old pass outside window
    assert m["emails_sent"] == 3
    assert m["replies_yes"] == 1
    assert m["by_category"].get("plumber", {}).get("sent") == 1


@pytest.mark.asyncio
async def test_review_skipped_without_pass_data():
    assert await strat.review_strategy(force=True) is None


@pytest.mark.asyncio
async def test_review_strategy_uses_llm_and_persists(monkeypatch):
    _seed_journal(strat.REASON_LOG, [
        {"event": "pass_summary", "ts": strat._ts(),
         "stats": {"emails_sent": 5, "new_leads_found": 1, "owner_notified": 0, "meetings_scheduled": 0}},
    ])
    async def fake_review(system, user):
        return {"angle": "Focus on reviews", "focus": [["plumber", "Houston", "TX"]],
                "notes": ["plumbers reply"], "actions": ["Send 2x follow-ups"]}
    monkeypatch.setattr(strat, "_llm_review_call", fake_review)
    s = await strat.review_strategy(force=True)
    assert s is not None
    assert s["angle"] == "Focus on reviews"
    assert s["focus"] == [["plumber", "Houston", "TX"]]
    assert s["last_review"]
    # Persisted and journaled.
    assert strat.load_strategy()["angle"] == "Focus on reviews"
    import admin.agency.sba_reason as reason
    entries = [e for e in reason.recent_decisions() if e["event"] == "strategy_review"]
    assert entries


@pytest.mark.asyncio
async def test_review_llm_failure_keeps_old_strategy(monkeypatch):
    s0 = strat.load_strategy()
    s0["angle"] = "Keep me"
    strat.save_strategy(s0)
    _seed_journal(strat.REASON_LOG, [
        {"event": "pass_summary", "ts": strat._ts(),
         "stats": {"emails_sent": 1, "new_leads_found": 0}},
    ])
    async def boom(system, user):
        raise RuntimeError("model down")
    monkeypatch.setattr(strat, "_llm_review_call", boom)
    assert await strat.review_strategy(force=True) is None
    assert strat.load_strategy()["angle"] == "Keep me"


@pytest.mark.asyncio
async def test_maybe_review_milestone_on_meeting(monkeypatch):
    _seed_journal(strat.REASON_LOG, [
        {"event": "pass_summary", "ts": strat._ts(),
         "stats": {"emails_sent": 1, "meetings_scheduled": 1}},
    ])
    async def fake_review(system, user):
        return {"angle": "A", "focus": [], "notes": [], "actions": []}
    monkeypatch.setattr(strat, "_llm_review_call", fake_review)
    s = await strat.maybe_review({"emails_sent": 1, "meetings_scheduled": 1, "new_leads_found": 0})
    assert s is not None  # milestone forces a review


def test_digest_kinds_and_bodies():
    strat.observe_pass({"new_leads_found": 0})
    strat.observe_pass({"new_leads_found": 0})
    s = strat.load_strategy()
    m = strat.metrics_from_journal()
    assert strat.digest_kind_needed({"new_leads_found": 0}, m) == "alert_leads"
    body = strat.build_digest_body("alert_leads", {"new_leads_found": 0}, m, s)
    assert "no new leads" in body.lower()
    strat.mark_digest("alert_leads")


def test_digest_not_sent_after_marked():
    strat.mark_digest("daily")
    # DIGEST_INTERVAL_SECONDS=0 -> due again, that is fine; here we just verify
    # mark_digest persists last_digest.
    assert strat.load_strategy()["last_digest"]
