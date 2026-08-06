"""Tests for organic post history + real scheduler (P0)."""
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from admin.tools.organic import history as hist
from admin.tools.organic import scheduler as sched


@pytest.fixture()
def tmp_data(monkeypatch, tmp_path):
    """Point ORGANIC_DATA_DIR at a temp dir so tests stay hermetic."""
    monkeypatch.setattr(hist, "ORGANIC_DATA_DIR", tmp_path)
    monkeypatch.setattr(sched, "ORGANIC_DATA_DIR", tmp_path)
    return tmp_path


def _published(channel="reddit", **over):
    r = {"status": "published", "channel": channel, "post_id": "p1", "post_url": "https://x/p1", "error": ""}
    r.update(over)
    return r


# ── history ─────────────────────────────────────────────────────────────────

def test_record_and_list(tmp_data):
    hid = hist.record_post("ws1", "reddit", _published(), {"subreddit": "r/test", "title": "T", "body": "B"})
    assert hid
    posts = hist.list_posts("ws1")
    assert len(posts) == 1
    assert posts[0]["channel"] == "reddit"
    assert posts[0]["payload"]["subreddit"] == "r/test"
    assert posts[0]["payload"].get("password") is None


def test_list_filters_channel_and_sorts_newest_first(tmp_data):
    hist.record_post("ws1", "reddit", _published(), {"title": "older"})
    hist.record_post("ws1", "telegram", _published(channel="telegram"), {"text": "newer"})
    posts = hist.list_posts("ws1")
    assert [p["channel"] for p in posts] == ["telegram", "reddit"]
    reddit_only = hist.list_posts("ws1", channel="reddit")
    assert len(reddit_only) == 1


def test_history_stats(tmp_data):
    hist.record_post("ws1", "reddit", _published())
    hist.record_post("ws1", "reddit", _published())
    hist.record_post("ws1", "telegram", {"status": "error", "channel": "telegram", "error": "nope", "post_id": "", "post_url": ""})
    stats = hist.history_stats("ws1")
    assert stats["total"] == 3
    assert stats["published"] == 2
    assert stats["by_channel"] == {"reddit": 2, "telegram": 1}
    assert stats["by_status"]["error"] == 1


def test_record_fail_open_when_dir_unwritable(tmp_data):
    with patch("admin.tools.organic.history._history_file", side_effect=OSError("disk full")):
        hid = hist.record_post("ws1", "reddit", _published())
    assert hid  # returns synthetic id, never raises


# ── scheduler ───────────────────────────────────────────────────────────────

def test_schedule_validates_channel_and_fields(tmp_data):
    r = sched.schedule_post("ws1", "nope", {}, "2026-08-06T18:00:00Z")
    assert r["status"] == "error"
    assert "Unknown channel" in r["error"]

    r = sched.schedule_post("ws1", "reddit", {}, "2026-08-06T18:00:00Z")
    assert r["status"] == "error"
    assert "Missing required fields" in r["error"]


def test_schedule_bad_datetime(tmp_data):
    r = sched.schedule_post("ws1", "reddit", {"subreddit": "t", "title": "x", "body": "y"}, "not-a-date")
    assert r["status"] == "error"


def test_schedule_and_list(tmp_data):
    run_at = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    r = sched.schedule_post("ws1", "reddit", {"subreddit": "t", "title": "x", "body": "y"}, run_at)
    assert r["status"] == "scheduled"
    assert r["schedule_id"]
    listed = sched.list_scheduled("ws1")
    assert len(listed) == 1
    assert listed[0]["status"] == "pending"
    assert listed[0]["channel"] == "reddit"


def test_cancel_scheduled(tmp_data):
    run_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    r = sched.schedule_post("ws1", "reddit", {"subreddit": "t", "title": "x", "body": "y"}, run_at)
    cancel = sched.cancel_scheduled("ws1", r["schedule_id"])
    assert cancel["status"] == "cancelled"
    assert sched.list_scheduled("ws1") == []
    assert sched.cancel_scheduled("ws1", "missing")["status"] == "error"


def test_dispatch_due_posts_and_records_history(tmp_data):
    past = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    future = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    sched.schedule_post("ws1", "reddit", {"subreddit": "t", "title": "x", "body": "y"}, past)
    sched.schedule_post("ws1", "reddit", {"subreddit": "t", "title": "x", "body": "y"}, future)

    with patch("admin.tools.organic.hub.post") as mock_post:
        mock_post.return_value = _published()
        stats = sched.dispatch_due()
    assert stats["due"] == 1
    assert stats["dispatched"] == 1
    assert stats["failed"] == 0

    # pending file removed, history recorded
    assert len(sched.list_scheduled("ws1")) == 1  # only the future one remains
    posts = hist.list_posts("ws1")
    assert len(posts) == 1
    assert posts[0]["scheduled_for"] == past


def test_dispatch_records_failures(tmp_data):
    past = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    sched.schedule_post("ws1", "reddit", {"subreddit": "t", "title": "x", "body": "y"}, past)
    with patch("admin.tools.organic.hub.post") as mock_post:
        mock_post.return_value = {"status": "error", "error": "auth failed"}
        stats = sched.dispatch_due()
    assert stats["failed"] == 1
    assert stats["errors"][0]["error"] == "auth failed"
    posts = hist.list_posts("ws1")
    assert posts[0]["status"] == "error"


def test_dispatch_due_uses_hub_post_success_shape(tmp_data):
    # hub.post returns a dict; dispatch must pass it through to history
    past = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    sched.schedule_post("ws1", "telegram", {"text": "hi"}, past)
    with patch("admin.tools.organic.hub.post", return_value={"status": "published", "channel": "telegram", "post_url": "https://t.me/x/1"}):
        stats = sched.dispatch_due()
    assert stats["dispatched"] == 1
    posts = hist.list_posts("ws1")
    assert posts[0]["post_url"] == "https://t.me/x/1"


def test_dispatch_ignores_future_jobs(tmp_data):
    future = (datetime.now(timezone.utc) + timedelta(hours=3)).isoformat()
    sched.schedule_post("ws1", "reddit", {"subreddit": "t", "title": "x", "body": "y"}, future)
    with patch("admin.tools.organic.hub.post") as mock_post:
        stats = sched.dispatch_due()
    mock_post.assert_not_called()
    assert stats["due"] == 0
