# admin/tests/test_organic_reddit.py
from unittest.mock import patch

from admin.tools.organic.base import PostResult
from admin.tools.organic.reddit_api import post, _get_access_token


def test_post_no_config_returns_config_missing():
    with patch("admin.tools.organic.reddit_api.get_active_token", return_value=None):
        with patch("admin.tools.organic.reddit_api.get_channel_config", return_value={}):
            result = post("ws1", {"subreddit": "r/test", "title": "t", "body": "b"})
    assert result.status == "config_missing"
    assert "token" in result.error


def test_get_access_token_ok():
    with patch("admin.tools.organic.reddit_api.requests.post") as mock_post:
        mock_post.return_value.ok = True
        mock_post.return_value.json.return_value = {"access_token": "tok123", "expires_in": 3600}
        tok = _get_access_token("cid", "csec", "user", "pass")
    assert tok == "tok123"


def test_get_access_token_fails():
    with patch("admin.tools.organic.reddit_api.requests.post") as mock_post:
        mock_post.return_value.ok = False
        mock_post.return_value.text = "bad creds"
        tok = _get_access_token("cid", "csec", "user", "pass")
    assert tok is None
