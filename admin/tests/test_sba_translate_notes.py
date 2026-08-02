# admin/tests/test_sba_translate_notes.py
"""Tests for meeting speech-to-speech + notes flow (sba_translate + sba routes)."""
import base64
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from admin.tools.sba_translate import SBATranslationEngine, _mock_wav_bytes, _tts_provider


@pytest.fixture
def engine():
    os.environ["SBA_TTS_PROVIDER"] = "mock"
    return SBATranslationEngine()


# ── mock TTS helpers ────────────────────────────────────────────────────────


def test_mock_wav_is_valid_wav():
    data = _mock_wav_bytes()
    assert data[:4] == b"RIFF"
    assert data[8:12] == b"WAVE"
    assert len(data) > 44


def test_tts_provider_default_mock():
    os.environ.pop("SBA_TTS_PROVIDER", None)
    assert _tts_provider() == "mock"


@pytest.mark.asyncio
async def test_synthesize_mock_returns_audio(engine):
    out = await engine.synthesize("Namaste ji", lang="en")
    assert out["provider"] == "mock"
    audio = base64.b64decode(out["audio_b64"])
    assert audio[:4] == b"RIFF"
    assert out["lang"] == "en"


@pytest.mark.asyncio
async def test_synthesize_falls_back_to_mock_on_unknown_provider(engine):
    os.environ["SBA_TTS_PROVIDER"] = "bogus-provider"
    out = await engine.synthesize("Hello")
    assert out["provider"] == "mock"
    os.environ["SBA_TTS_PROVIDER"] = "mock"


# ── process_meeting: notes file + meeting record ───────────────────────────


@pytest.mark.asyncio
async def test_process_meeting_writes_notes_file(engine, tmp_path, monkeypatch):
    """With no meeting_id, notes go to a timestamped md file."""
    async def fake_transcribe(path):
        return [
            {"speaker": "Client", "text": "Hello, how much?", "timestamp": "00:01"},
            {"speaker": "Owner", "text": "Pricing package hai", "timestamp": "00:05"},
        ]

    async def fake_translate(segments):
        for s in segments:
            s["translation"] = "translated:" + s["text"]
        return segments

    async def fake_summary(segments):
        return {
            "key_points": ["price asked"],
            "action_items": [{"task": "send quote", "owner": "owner"}],
            "decisions": [],
            "next_steps": ["share pricing"],
            "full_summary": "Client ne pricing poochi",
        }

    monkeypatch.setattr(engine, "transcribe_audio", fake_transcribe)
    monkeypatch.setattr(engine, "translate_meeting_live", fake_translate)
    monkeypatch.setattr(engine, "generate_summary", fake_summary)

    # temp fake audio file
    audio_path = str(tmp_path / "meeting.wav")
    with open(audio_path, "wb") as f:
        f.write(_mock_wav_bytes())

    result = await engine.process_meeting(audio_path, meeting_id=None, notes_dir=str(tmp_path))
    assert result["saved_to_meeting"] is False
    assert result["notes_file"] and os.path.exists(result["notes_file"])
    content = open(result["notes_file"], encoding="utf-8").read()
    assert "Client" in content
    assert "translated:Hello" in content
    assert "price asked" in content


@pytest.mark.asyncio
async def test_process_meeting_saves_notes_to_meeting(engine, tmp_path, monkeypatch):
    """With meeting_id, translated segments + summary are appended to the meeting."""
    from admin.agency import sba_store

    added = []

    async def fake_add_note(mid, text, language, speaker):
        added.append({"mid": mid, "text": text, "language": language, "speaker": speaker})

    async def fake_transcribe(path):
        return [{"speaker": "Client", "text": "Ok book it", "timestamp": "00:02"}]

    async def fake_translate(segments):
        for s in segments:
            s["translation"] = "haan book karo"
        return segments

    async def fake_summary(segments):
        return {"key_points": [], "action_items": [], "decisions": [], "next_steps": [],
                "full_summary": "Booked"}

    monkeypatch.setattr(engine, "transcribe_audio", fake_transcribe)
    monkeypatch.setattr(engine, "translate_meeting_live", fake_translate)
    monkeypatch.setattr(engine, "generate_summary", fake_summary)
    monkeypatch.setattr(sba_store, "add_meeting_note", fake_add_note)

    audio_path = str(tmp_path / "m2.wav")
    with open(audio_path, "wb") as f:
        f.write(_mock_wav_bytes())

    result = await engine.process_meeting(audio_path, meeting_id="m-9", notes_dir=str(tmp_path))
    assert result["saved_to_meeting"] is True
    assert len(added) == 2  # 1 segment + 1 summary
    assert added[0]["mid"] == "m-9"
    assert added[0]["speaker"] == "Client"
    assert "haan book karo" in added[0]["text"]
    assert "Booked" in added[1]["text"]


# ── routes smoke: page + registered handlers ───────────────────────────────


def test_translate_page_route_registered():
    from admin.api.routes import sba as routes_mod

    paths = [getattr(r, "path", "") for r in routes_mod.router.routes]
    assert "/api/sba/meetings/translate-page" in paths
    assert "/api/sba/meetings/audio/translate" in paths
    assert "/api/sba/meetings/process" in paths
    assert "/api/sba/meetings/tts" in paths
