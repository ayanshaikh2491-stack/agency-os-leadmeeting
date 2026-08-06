# admin/tests/test_organic_reddit.py
from unittest.mock import patch

from admin.tools.organic.base import PostResult
from admin.tools.organic.reddit_api import post, _get_access_token


def _mock_creds():
    patcher_token = patch("admin.tools.organic.reddit_api.get_active_token", return_value={"access_token": "tok"})
    patcher_cfg = patch("admin.tools.organic.reddit_api.get_channel_config", return_value={
        "client_id": "cid", "client_secret": "csec", "username": "user", "password": "pass",
    })
    patcher_auth = patch("admin.tools.organic.reddit_api._get_access_token", return_value="access123")
    patcher_submit = patch("admin.tools.organic.reddit_api.requests.post")
    patcher_token.start()
    patcher_cfg.start()
    patcher_auth.start()
    mock_submit = patcher_submit.start()
    mock_submit.return_value.ok = True
    mock_submit.return_value.json.return_value = {"json": {"data": {"id": "abc123", "name": "t3_abc123"}}}
    return mock_submit


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


def test_post_success_with_dict_token():
    mock_submit = _mock_creds()
    result = post("ws1", {"subreddit": "r/test", "title": "t", "body": "b"})
    assert result.status == "published"
    assert result.post_id == "abc123"
    assert result.post_url == "https://www.reddit.com/r/test/comments/abc123"


def test_post_http200_json_errors_returns_error():
    mock_submit = _mock_creds()
    mock_submit.return_value.json.return_value = {
        "json": {"errors": [["RATELIMIT", "you are doing that too much"]]}
    }
    result = post("ws1", {"subreddit": "r/test", "title": "t", "body": "b"})
    assert result.status == "error"
    assert "RATELIMIT" in result.error


def test_subreddit_normalization():
    mock_submit = _mock_creds()
    post("ws1", {"subreddit": "reddit.com/r/test", "title": "t", "body": "b"})
    sent = mock_submit.call_args.kwargs["data"]
    assert sent["sr"] == "test"
    post("ws1", {"subreddit": "/r/rust", "title": "t", "body": "b"})
    sent = mock_submit.call_args.kwargs["data"]
    assert sent["sr"] == "rust"
