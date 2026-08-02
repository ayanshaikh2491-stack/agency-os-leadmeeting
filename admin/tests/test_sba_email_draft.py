# admin/tests/test_sba_email_draft.py
import pytest

from admin.tools.sba_email_draft import draft_email, fallback_email


def test_fallback_email_has_subject_and_body():
    lead = {"name": "Bob's Plumbing", "category": "plumber"}
    subject, body = fallback_email(lead)
    assert subject
    assert "Bob's Plumbing" in body


def test_fallback_email_works_with_missing_fields():
    subject, body = fallback_email({})
    assert subject and body


@pytest.mark.asyncio
async def test_draft_email_falls_back_when_llm_fails(monkeypatch):
    async def boom(**kwargs):
        raise RuntimeError("no llm")

    monkeypatch.setattr("admin.tools.sba_email_draft._llm_draft", boom)
    lead = {"name": "Dominguez Electric", "category": "electrician", "city": "Houston", "state": "TX"}
    subject, body = await draft_email(lead)
    assert subject and body
    assert "Dominguez" in body
