"""SBA pipeline smoke tests: email client, meeting manager, translation engine, tools, graph.

Run: python -m pytest admin/tests/test_sba_pipeline.py -q
(or directly: python admin/tests/test_sba_pipeline.py)
"""
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import pytest


def test_email_client_surface():
    from admin.tools.sba_email_client import SBAEmailClient, OWNER_NAME, OWNER_EMAIL

    client = SBAEmailClient()
    assert isinstance(client.enabled, bool)
    for m in ("send_email", "check_replies"):
        assert callable(getattr(client, m))
    assert isinstance(OWNER_NAME, str)


def test_email_templates():
    from admin.tools.sba_email_templates import (
        TEMPLATE_FIRST_CONTACT,
        TEMPLATE_MEETING_CONFIRM,
        TEMPLATE_OWNER_NOTIFICATION,
        format_template,
    )

    assert "{lead_name}" in TEMPLATE_FIRST_CONTACT
    assert "{meeting_link}" in TEMPLATE_MEETING_CONFIRM
    out = format_template("first_contact", lead_name="X", platform="Upwork", project_type="SEO",
                          service_description="SEO", sample_result="2x traffic",
                          owner_name="Ayan", owner_email="a@b.c")
    assert "X" in out
    with pytest.raises(ValueError):
        format_template("nope")


def test_meeting_manager_surface():
    from admin.tools.sba_meeting import SBAMeetingManager

    mgr = SBAMeetingManager()
    for m in ("create_meeting", "update_meeting_status", "add_meeting_summary",
              "add_meeting_note", "get_meetings", "get_meeting"):
        assert callable(getattr(mgr, m)), m


def test_translation_engine_surface():
    from admin.tools.sba_translate import SBATranslationEngine

    eng = SBATranslationEngine()
    for m in ("translate_for_owner", "translate_for_client", "transcribe_audio",
              "generate_summary", "translate_meeting_live"):
        assert callable(getattr(eng, m)), m


def test_sba_tools_registry():
    from admin.workspace.agents.sba import SBA_ALL_TOOLS, SBA_EMAIL_TOOLS

    names = [t["function"]["name"] for t in SBA_ALL_TOOLS]
    for expected in ("detect_lead_sources", "save_lead_record", "qualify_lead",
                     "update_lead_info", "send_lead_email", "check_lead_replies",
                     "create_meeting", "translate_for_owner", "translate_for_client",
                     "generate_meeting_summary"):
        assert expected in names, expected
    assert len(names) == len(set(names)), "duplicate tool names"
    # Every tool schema must be Groq-compatible
    for t in SBA_ALL_TOOLS:
        fn = t["function"]
        assert t["type"] == "function"
        assert isinstance(fn.get("description"), str)
        assert fn["parameters"].get("type") == "object"


def test_sba_tool_dispatch():
    from admin.tools.sba_tools import SBA_TOOL_DISPATCH, execute_sba_tool

    async def _run():
        assert "update_lead_info" in SBA_TOOL_DISPATCH
        res = await execute_sba_tool("list_saved_leads", {})
        assert isinstance(res, (dict, list))
        return True

    assert asyncio.run(_run())


def test_sba_graph_builds():
    from admin.workspace.agents.sba import build_sba_workspace_graph, SBA_SYSTEM_PROMPT

    # Prompt must format with no KeyError and keep JSON example readable
    formatted = SBA_SYSTEM_PROMPT.format(workspace_name="W", client_name="C")
    assert "TOOL CALL FORMAT" in formatted
    assert '{"key": "value"}' in formatted

    graph = build_sba_workspace_graph()
    assert graph is not None


def test_sba_store_update_merge():
    """update_lead merges context/notes instead of replacing them."""
    import asyncio

    from admin.agency import sba_store

    async def _run():
        lead = await sba_store.create_lead(
            {
                "name": "Merge Test",
                "business_name": "Merge Co",
                "source": "test",
            }
        )
        lid = lead["id"]
        await sba_store.update_lead(lid, {"context": {"industry": "d2c"}})
        await sba_store.update_lead(lid, {"context": {"needs": ["seo"]}})
        got = sba_store.get_lead(lid)
        assert got["context"].get("industry") == "d2c"
        assert got["context"].get("needs") == ["seo"]
        return True

    assert asyncio.run(_run())


def test_orchestrator_sba_functions_exist():
    import inspect

    import admin.agency.orchestrator as orch

    assert callable(getattr(orch, "sba_pipeline_scan", None))
    assert callable(getattr(orch, "sba_check_email_leads", None))
    assert callable(getattr(orch, "ceo_process_sba_handoff", None))
    assert inspect.iscoroutinefunction(orch.sba_check_email_leads)
    assert inspect.iscoroutinefunction(orch.ceo_process_sba_handoff)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
