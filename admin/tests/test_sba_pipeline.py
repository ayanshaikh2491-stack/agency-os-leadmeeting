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


def test_sba_meeting_uses_correct_gws_argv():
    """Regression guard for the SBA meeting booking bug.

    The gws CLI requires `calendar +insert` (not `insert`) with
    `--summary/--start/--end/--attendee/--meet` flags. The old code used
    `insert --title --duration --conference --attendees`, which the real CLI
    rejects, so every meeting silently fell back to a FAKE meet link. This
    test captures the argv actually passed to asyncio.create_subprocess_exec
    and asserts the corrected command shape, so the bug can't return.
    """
    import asyncio
    import subprocess

    captured = []

    class _FakeProc:
        def _comm(self):
            out = (
                '{"htmlLink":"x","hangoutLink":"https://meet.google.com/abc-defg-hij"}'
            ).encode()
            return (out, b"")

    async def _fake_exec(*args, **kwargs):
        captured.append(list(args))
        proc = _FakeProc()
        # communicate() must be awaitable, matching asyncio subprocess API.
        proc.communicate = lambda timeout=None: _await(proc._comm())
        return proc

    async def _await(val):
        return val

    from admin.tools import sba_meeting as mm_mod

    monkeypatch_exec = _make_exec_patch(_fake_exec)

    async def _run():
        with monkeypatch_exec():
            mgr = mm_mod.SBAMeetingManager(email_client=_FakeEmail())
            meeting = await mgr.create_meeting(
                lead_id="L1", lead_name="Test Lead",
                lead_email="lead@example.com",
                proposed_time="2026-08-20T04:30:00+00:00",
                duration_minutes=30,
            )
            return meeting

    meeting = asyncio.run(_run())

    # A real Meet link must come back (not a fake placeholder).
    # notes[0] = calendar event, notes[1] = meeting link.
    notes = meeting.get("notes", [])
    link_note = next((n for n in notes if n.get("type") == "meeting_link"), {})
    assert "meet.google.com" in link_note.get("url", "")

    # Two gws calls: placeholder Meet link + calendar event.
    gws_calls = [c for c in captured if c[:1] == ["gws"]]
    assert len(gws_calls) == 2, f"expected 2 gws calls, got {len(gws_calls)}"

    # The placeholder (call 0) uses `now()`; the calendar event (call 1) must
    # use the proposed time and a derived end time.
    event_call = gws_calls[1]
    for call in gws_calls:
        # Must use the real subcommand and real flags.
        assert "+insert" in call, f"must use 'calendar +insert', got {call}"
        assert "--summary" in call, f"missing --summary in {call}"
        assert "--start" in call, f"missing --start in {call}"
        assert "--end" in call, f"missing --end in {call}"
        assert "--attendee" in call, f"missing --attendee in {call}"
        assert "--meet" in call, f"missing --meet in {call}"
        # The broken flags must never appear again.
        assert "--title" not in call, f"--title is invalid gws flag: {call}"
        assert "--duration" not in call, f"--duration is invalid gws flag: {call}"
        assert "--conference" not in call, f"--conference is invalid gws flag: {call}"
        assert "--attendees" not in call, f"--attendees (plural) is invalid: {call}"

    # Calendar event must carry start+end (derived from proposed time + duration).
    idx = event_call.index("--start")
    assert event_call[idx + 1] == "2026-08-20T04:30:00+00:00"
    eidx = event_call.index("--end")
    assert eidx + 1 < len(event_call)
    # end = start + 30min
    assert event_call[eidx + 1] == "2026-08-20T05:00:00+00:00"


def test_sba_meeting_no_silent_fake_link_on_gws_failure():
    """Guard: when gws cannot book a real meeting, we must NOT send a fake link.

    The old code fabricated `meet.google.com/<date>-sba-mtg` and reported
    success. The hardened code raises RuntimeError (and the meeting module
    records a pending manual booking + alerts the owner) so a fake "confirmed"
    meeting can never be reported.
    """
    import asyncio

    # gws returns NO meet link (simulates missing/unauthenticated CLI).
    class _NoLinkProc:
        def communicate(self, timeout=None):
            async def _c():
                return (b"", b"no meet link returned")
            return _c()

    async def _fake_exec_no_link(*args, **kwargs):
        return _NoLinkProc()

    from admin.tools import sba_meeting as mm_mod

    async def _run():
        with _make_exec_patch(_fake_exec_no_link)():
            mgr = mm_mod.SBAMeetingManager(email_client=_FakeEmailAlert())
            try:
                await mgr.create_meeting(
                    lead_id="LX", lead_name="No Link Lead",
                    lead_email="nolead@example.com",
                    proposed_time="2026-08-20T04:30:00+00:00",
                    duration_minutes=30,
                )
                return "no_error"
            except RuntimeError as exc:
                return f"raised:{exc}"

    res = asyncio.run(_run())
    assert res.startswith("raised:"), f"expected RuntimeError on gws failure, got {res!r}"


class _FakeEmailAlert:
    enabled = True

    async def send_email(self, *args, **kwargs):
        # Captured by the meeting module's pending-booking owner notification.
        return True


def _make_exec_patch(fake_exec):
    """Return a context manager that monkeypatches asyncio.create_subprocess_exec."""
    from contextlib import contextmanager

    @contextmanager
    def _cm():
        import asyncio

        orig = asyncio.create_subprocess_exec
        asyncio.create_subprocess_exec = fake_exec
        try:
            yield
        finally:
            asyncio.create_subprocess_exec = orig

    return _cm


class _FakeEmail:
    enabled = True

    async def send_email(self, *args, **kwargs):
        return True


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
