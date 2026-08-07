# admin/tests/test_sba_reason.py
"""Tests for the LLM reasoning layer (sba_reason.py).

The layer must never hang and must fall back to deterministic rules when the
model is slow or unavailable, so these tests mock `_llm_call` to simulate
both model verdicts and model failures.
"""
import pytest

from admin.agency import sba_reason as reason


# ── judge_lead ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_judge_lead_parses_model_verdict(monkeypatch):
    async def fake_llm(system, user, timeout=reason.REASON_TIMEOUT_SECONDS):
        return {"score": 82, "action": "contact", "reason": "local plumber, no website, high need"}

    monkeypatch.setattr(reason, "_llm_call", fake_llm)
    verdict = await reason.judge_lead({
        "name": "Cooper Plumbing",
        "category": "plumber",
        "city_state": "Austin, TX",
    })
    assert verdict["score"] == 82
    assert verdict["action"] == "contact"
    assert "plumber" in verdict["reason"]


@pytest.mark.asyncio
async def test_judge_lead_clamps_score_to_0_100(monkeypatch):
    async def fake_llm(system, user, timeout=reason.REASON_TIMEOUT_SECONDS):
        return {"score": 999, "action": "wait", "reason": "scores are clamped"}

    monkeypatch.setattr(reason, "_llm_call", fake_llm)
    verdict = await reason.judge_lead({"name": "Huge Corp", "category": "restaurant"})
    assert verdict["score"] == 100
    assert verdict["action"] == "wait"


@pytest.mark.asyncio
async def test_judge_lead_falls_back_when_model_down(monkeypatch):
    async def broken_llm(system, user, timeout=reason.REASON_TIMEOUT_SECONDS):
        raise RuntimeError("model unreachable")

    monkeypatch.setattr(reason, "_llm_call", broken_llm)
    verdict = await reason.judge_lead({"name": "Any Biz", "category": "plumber"})
    # Same behaviour as before the reasoning layer: never block on a flaky model.
    assert verdict["score"] == 50
    assert verdict["action"] == "contact"


@pytest.mark.asyncio
async def test_judge_lead_skips_empty_name():
    verdict = await reason.judge_lead({"name": "", "category": "plumber"})
    assert verdict["action"] == "skip"
    assert verdict["score"] == 0


# ── verify_email ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_verify_email_blocks_foreign_mailbox(monkeypatch):
    async def fake_llm(system, user, timeout=reason.REASON_TIMEOUT_SECONDS):
        return {"ok": False, "confidence": 0.9, "reason": "parent brand mailbox, not the local shop"}

    monkeypatch.setattr(reason, "_llm_call", fake_llm)
    verdict = await reason.verify_email("Cooper Plumbing", "info@hugecorp.com")
    assert verdict["ok"] is False
    assert verdict["confidence"] == 0.9


@pytest.mark.asyncio
async def test_verify_email_falls_back_ok_when_model_down(monkeypatch):
    async def broken_llm(system, user, timeout=reason.REASON_TIMEOUT_SECONDS):
        raise RuntimeError("model unreachable")

    monkeypatch.setattr(reason, "_llm_call", broken_llm)
    verdict = await reason.verify_email("Cooper Plumbing", "cooper@gmail.com")
    # A flaky model must never silently block a legitimate mailbox.
    assert verdict["ok"] is True


# ── understand_reply ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_understand_reply_extracts_meeting_time(monkeypatch):
    async def fake_llm(system, user, timeout=reason.REASON_TIMEOUT_SECONDS):
        return {"intent": "yes", "meeting_time": "15:00", "reason": "owner wants 3pm call"}

    monkeypatch.setattr(reason, "_llm_call", fake_llm)
    rep = await reason.understand_reply("call me at 3 pm")
    assert rep["intent"] == "yes"
    assert rep["meeting_time"] == "15:00"


@pytest.mark.asyncio
async def test_understand_reply_rejects_bad_time_format(monkeypatch):
    async def fake_llm(system, user, timeout=reason.REASON_TIMEOUT_SECONDS):
        return {"intent": "yes", "meeting_time": "tomorrow morning", "reason": "vague"}

    monkeypatch.setattr(reason, "_llm_call", fake_llm)
    rep = await reason.understand_reply("tomorrow morning works")
    assert rep["meeting_time"] == ""


@pytest.mark.asyncio
async def test_understand_reply_falls_back_to_keyword_classifier(monkeypatch):
    async def broken_llm(system, user, timeout=reason.REASON_TIMEOUT_SECONDS):
        raise RuntimeError("model unreachable")

    monkeypatch.setattr(reason, "_llm_call", broken_llm)
    rep = await reason.understand_reply("yes sounds good, let's talk")
    assert rep["intent"] == "yes"
    assert rep["meeting_time"] == ""


# ── prioritize ────────────────────────────────────────────────────────────


def test_prioritize_sorts_by_score_unknown_is_50():
    leads = [
        {"name": "low", "raw": {"lead_score": 30}},
        {"name": "high", "raw": {"lead_score": 90}},
        {"name": "none", "raw": {}},
        {"name": "junk", "raw": {"lead_score": "abc"}},
    ]
    ordered = [l["name"] for l in reason.prioritize(leads)]
    assert ordered == ["high", "none", "junk", "low"]


# ── journal ───────────────────────────────────────────────────────────────


def test_log_and_recent_decisions_roundtrip(tmp_path, monkeypatch):
    log = tmp_path / "reasoning.jsonl"
    monkeypatch.setattr(reason, "REASON_LOG", str(log))

    reason.log_decision({"event": "lead_judged", "name": "A"})
    reason.log_decision({"event": "pass_summary", "stats": {"emails_sent": 1}})
    reason.log_decision({"event": "lead_judged", "name": "B"})

    all_events = reason.recent_decisions(limit=10)
    assert len(all_events) == 3
    assert all_events[0]["name"] == "B"  # newest first

    filtered = reason.recent_decisions(limit=10, event="lead_judged")
    assert [e["name"] for e in filtered] == ["B", "A"]

    assert reason.recent_decisions(limit=2, event="email_sent") == []
