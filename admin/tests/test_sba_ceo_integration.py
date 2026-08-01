"""SBA CEO integration tests — monitor, email service, pipeline scan, handoff E2E.

Covers the post-plan additions (sba_monitor, email_service, orchestrator
pipeline functions) plus the loop-lifecycle fix (persistence connection is
closed after fire-and-forget writes in script mode, so processes exit cleanly).
"""
import asyncio
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, r"C:\Users\TAUSHEF\Downloads\int")


# ── SBAMonitor ───────────────────────────────────────────────────────────


def test_monitor_build_status_shape():
    from admin.agency.sba_monitor import SBAMonitor

    async def go():
        status = await SBAMonitor()._build_status()
        return status

    status = asyncio.run(go())
    assert "pipeline" in status
    assert "total_leads" in status
    assert "hot_leads" in status
    assert "stale_leads" in status
    assert "pending_handoffs" in status
    assert "alerts" in status


# ── EmailLeadService ─────────────────────────────────────────────────────


def test_email_service_disabled_when_not_configured():
    from admin.tools.email_service import EmailLeadService

    os.environ.pop("SBA_EMAIL_ENABLED", None)

    async def go():
        svc = EmailLeadService()
        assert svc.enabled is False
        assert await svc.check_inbox() == []
        assert await svc.process_and_create_leads() == []

    asyncio.run(go())


def test_email_service_auto_reply_detection():
    from admin.tools.email_service import EmailLeadService

    svc = EmailLeadService()
    assert svc._is_auto_reply("Out of Office", "a@b.com") is True
    assert svc._is_auto_reply("RE: Your proposal", "a@b.com") is False
    assert svc._is_auto_reply("Newsletter", "no-reply@news.com") is True
    assert svc._extract_email("John <john@example.com>") == "john@example.com"
    assert svc._extract_email("john@example.com") == "john@example.com"


# ── Orchestrator pipeline scan ───────────────────────────────────────────


def test_sba_pipeline_scan():
    from admin.agency.orchestrator import sba_pipeline_scan

    result = sba_pipeline_scan("pytest_scan_ws")
    assert result.get("status") == "scanned"
    assert "total_leads" in result
    assert "pipeline" in result
    assert "hot_leads" in result
    assert "pending_handoffs" in result
    assert "report_id" in result


def test_sba_check_email_leads_disabled():
    from admin.agency.orchestrator import sba_check_email_leads

    os.environ.pop("SBA_EMAIL_ENABLED", None)

    async def go():
        return await sba_check_email_leads()

    result = asyncio.run(go())
    assert result.get("status") == "disabled"


# ── CEO handoff E2E ──────────────────────────────────────────────────────


def test_ceo_handoff_end_to_end():
    """Lead -> handoff -> CEO processes -> workspace created + bus write persists."""
    from admin.agency.orchestrator import ceo_process_sba_handoff
    from admin.agency.sba_store import create_handoff, create_lead, get_handoff
    from admin.workspace.agent_bus import get_messages

    async def go():
        lead = await create_lead({
            "name": "Pytest Client",
            "business_name": "Pytest Biz",
            "email": "pytest@example.com",
            "phone": "+91 00000 00000",
            "source": "pytest",
            "score": 88,
            "context": {
                "industry": "realestate",
                "needs": ["local seo"],
                "scope": "Local SEO, 3 months",
            },
        })
        handoff = await create_handoff(lead["id"], ceo_message="pytest handoff")
        assert handoff.get("brief", {}).get("industry") == "realestate"

        result = await ceo_process_sba_handoff(handoff["id"])
        assert result.get("status") == "workspace_created"
        assert result.get("workspace_id")
        assert result.get("agents_registered") == 7

        # Drain fire-and-forget writes so the bus message is persisted
        await asyncio.sleep(0.2)

        # Bus message landed
        msgs = get_messages(result["workspace_id"])
        assert any(m.message_type == "report" for m in msgs)

        # Handoff marked processed
        h2 = get_handoff(handoff["id"])
        assert h2.get("workspace_id") == result["workspace_id"]
        return result

    result = asyncio.run(go())
    assert result["workspace_id"]


# ── Loop lifecycle ───────────────────────────────────────────────────────


def test_send_message_exits_cleanly_after_asyncio_run():
    """Script-mode async send must close persistence so the process can exit."""
    from admin.workspace.agent_bus import send_message

    async def go():
        msg = send_message(
            from_agent="pytest", to_agent="content", workspace_id="ExitTest",
            subject="hi", content="hello", message_type="brief",
        )
        await asyncio.sleep(0.2)
        return msg

    msg = asyncio.run(go())
    assert msg.id
    # Second call in a fresh loop must work too (no cross-loop lock issues)
    msg2 = asyncio.run(go())
    assert msg2.id
