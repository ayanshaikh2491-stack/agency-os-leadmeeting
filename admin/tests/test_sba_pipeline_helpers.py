# admin/tests/test_sba_pipeline_helpers.py
from admin.agency.sba_pipeline import (
    classify_reply,
    is_owner,
    meeting_confirm_body,
    owner_notification_body,
    parse_owner_command,
    rejected_body,
    tomorrow,
)


def test_classify_reply_yes():
    assert classify_reply("Yes interested, call me") == "yes"
    assert classify_reply("Haan theek hai") == "yes"


def test_classify_reply_no():
    assert classify_reply("no thanks") == "no"
    assert classify_reply("Nahi, not right now") == "no"


def test_classify_reply_maybe():
    assert classify_reply("I will discuss this later") == "maybe"
    assert classify_reply("I will let you know") == "maybe"


def test_classify_reply_word_boundaries():
    # "no" inside "know" must not be "no"; "ok" inside "book" stays "yes"
    assert classify_reply("I will let you know") == "maybe"
    assert classify_reply("I want to book a meeting") == "yes"
    assert classify_reply("Please stop contacting me") == "no"
    assert classify_reply("Nahin bhai, thank you") == "no"


def test_parse_owner_command_haan():
    out = parse_owner_command("Re: lead 42", "Haan 3 baje")
    assert out["action"] == "haan"
    assert out["lead_id"] == "42"
    assert out["time"] == "15:00"


def test_parse_owner_command_nahi():
    out = parse_owner_command("Re: lead 7", "Nahi, next month")
    assert out["action"] == "nahi"


def test_tomorrow_iso():
    assert len(tomorrow()) == 10


def test_bodies_mention_lead():
    lead = {"name": "Bob's Plumbing", "category": "plumber"}
    assert "Bob" in owner_notification_body(lead, "hi")
    assert "Bob" in meeting_confirm_body(lead, "2026-08-05", "15:00")
    assert "Bob" in rejected_body(lead)


def test_is_owner_matches_configured_email(monkeypatch):
    monkeypatch.setenv("SBA_OWNER_EMAIL", "boss@example.com")
    assert is_owner("Boss <boss@example.com>")
    assert not is_owner("lead@example.com")
