from types import SimpleNamespace
from unittest.mock import patch

from admin.tools.organic.base import PostResult
from admin.tools.organic.hub import post


@patch("admin.tools.organic.hub._load_module", return_value=None)
def test_post_unknown_channel(mock_load):
    result = post("nope", "ws1", {})
    assert result["status"] == "error"
    assert "Unknown channel" in result["error"]


def test_post_missing_required_fields():
    result = post("reddit", "ws1", {"title": "t"})  # missing subreddit + body
    assert result["status"] == "error"
    assert "subreddit" in result["error"]
    assert "body" in result["error"]


@patch("admin.tools.organic.hub._load_module")
def test_post_routes_to_module(mock_load):
    fake_module = SimpleNamespace(post=lambda ws, payload: PostResult(channel="reddit", status="published", post_url="https://reddit.com/x"))
    mock_load.return_value = fake_module
    result = post("reddit", "ws1", {"subreddit": "r/test", "title": "t", "body": "b"})
    assert result["status"] == "published"
    assert result["post_url"] == "https://reddit.com/x"
