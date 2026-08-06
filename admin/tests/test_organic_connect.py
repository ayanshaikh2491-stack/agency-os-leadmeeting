"""Tests for organic channel connect flow (client credential onboarding)."""
from unittest.mock import patch

from admin.tools.organic.connect import (
    CREDENTIAL_FIELDS,
    channel_setup_status,
    save_channel_credentials,
)


# ── field catalog ──────────────────────────────────────────────────────────

def test_all_channels_have_connect_fields():
    from admin.tools.organic.registry import list_channels
    for ch in list_channels():
        assert ch["id"] in CREDENTIAL_FIELDS, f"missing connect fields for {ch['id']}"


# ── token channels ─────────────────────────────────────────────────────────

def test_save_linkedin_token():
    with patch("admin.tools.organic.connect.save_token") as mock_save:
        result = save_channel_credentials("ws1", "linkedin", {"access_token": "tok"})
    assert result["status"] == "connected"
    assert result["mode"] == "token"
    mock_save.assert_called_once()
    args = mock_save.call_args[1]
    assert args["platform"] == "linkedin"
    assert args["access_token"] == "tok"


def test_save_token_missing_errors():
    result = save_channel_credentials("ws1", "twitter", {})
    assert result["status"] == "error"
    assert "access_token" in result["error"]


def test_save_gbp_saves_location_config():
    with patch("admin.tools.organic.connect.save_token"), \
         patch("admin.tools.organic.connect.save_channel_config") as mock_cfg:
        result = save_channel_credentials("ws1", "gbp", {"access_token": "t", "location_name": "accounts/1/locations/2"})
    assert result["status"] == "connected"
    mock_cfg.assert_called_once_with("ws1", "gbp", {"location_name": "accounts/1/locations/2"})


# ── reddit script app ──────────────────────────────────────────────────────

def test_save_reddit():
    with patch("admin.tools.organic.connect.save_token") as mock_tok, \
         patch("admin.tools.organic.connect.save_channel_config") as mock_cfg:
        result = save_channel_credentials(
            "ws1", "reddit",
            {"client_id": "cid", "client_secret": "csec", "username": "user", "password": "pass",
             "subreddits": "r/test, r/other"},
        )
    assert result["status"] == "connected"
    tok = mock_tok.call_args[1]
    assert tok["platform_user_id"] == "cid"
    assert tok["platform_username"] == "user"
    cfg = mock_cfg.call_args[0][2]
    assert cfg["client_secret"] == "csec"
    assert cfg["subreddits"] == ["test", "other"]


def test_save_reddit_missing_errors():
    result = save_channel_credentials("ws1", "reddit", {"client_id": "cid"})
    assert result["status"] == "error"
    assert "client_secret" in result["error"]


# ── telegram bot ───────────────────────────────────────────────────────────

def test_save_telegram_verifies_bot():
    class FakeResp:
        ok = True

        def json(self):
            return {"result": {"username": "mybot", "id": 123}}

    with patch("admin.tools.organic.connect.requests.get", return_value=FakeResp()) as mock_get, \
         patch("admin.tools.organic.connect.save_token") as mock_tok, \
         patch("admin.tools.organic.connect.save_channel_config") as mock_cfg:
        result = save_channel_credentials("ws1", "telegram", {"bot_token": "tok", "chat_id": "-100abc"})
    assert result["status"] == "connected"
    assert result["bot"] == "mybot"
    mock_get.assert_called_once()
    tok = mock_tok.call_args[1]
    assert tok["access_token"] == "tok"
    mock_cfg.assert_called_once_with("ws1", "telegram", {"chat_id": "-100abc"})


def test_save_telegram_bad_token_errors():
    fake_resp = type("R", (), {"ok": False, "status_code": 401})()
    with patch("admin.tools.organic.connect.requests.get", return_value=fake_resp):
        result = save_channel_credentials("ws1", "telegram", {"bot_token": "bad"})
    assert result["status"] == "error"
    assert "rejected" in result["error"]


def test_save_telegram_missing_token_errors():
    result = save_channel_credentials("ws1", "telegram", {})
    assert result["status"] == "error"


# ── facebook ───────────────────────────────────────────────────────────────

def test_save_facebook_profile_dir():
    with patch("admin.tools.organic.connect.os.path.exists", return_value=True), \
         patch("admin.tools.organic.connect.save_channel_config") as mock_cfg:
        result = save_channel_credentials("ws1", "facebook", {"profile_dir": "/profiles/fb"})
    assert result["status"] == "connected"
    assert result["mode"] == "browser"
    mock_cfg.assert_called_once_with("ws1", "facebook", {"profile_dir": "/profiles/fb"})


def test_save_facebook_needs_creds():
    result = save_channel_credentials("ws1", "facebook", {})
    assert result["status"] == "error"
    assert "profile_dir" in result["error"]


def test_save_facebook_browser_login():
    fake_chrome = type("C", (), {
        "facebook_login": lambda self, e, p: _async_ok({"text": "✅ logged in, 5 cookies saved"}),
        "close": lambda self: _async_ok({"text": "ok"}),
    })()
    with patch("admin.tools.organic.connect._fb_default_profile_dir", return_value="/profiles/ws1"), \
         patch("admin.tools.organic.connect._new_chrome", return_value=fake_chrome), \
         patch("admin.tools.organic.connect.save_channel_config") as mock_cfg, \
         patch("admin.tools.organic.connect.os.makedirs"):
        result = save_channel_credentials("ws1", "facebook", {"email": "a@b.com", "password": "pw"})
    assert result["status"] == "connected"
    mock_cfg.assert_called_once()
    assert mock_cfg.call_args[0][2]["profile_dir"] == "/profiles/ws1"


def test_save_facebook_login_failure_errors():
    fake_chrome = type("C", (), {
        "facebook_login": lambda self, e, p: _async_ok({"error": "Facebook login failed"}),
        "close": lambda self: _async_ok({"text": "ok"}),
    })()
    with patch("admin.tools.organic.connect._fb_default_profile_dir", return_value="/profiles/ws1"), \
         patch("admin.tools.organic.connect._new_chrome", return_value=fake_chrome), \
         patch("admin.tools.organic.connect.os.makedirs"):
        result = save_channel_credentials("ws1", "facebook", {"email": "a@b.com", "password": "bad"})
    assert result["status"] == "error"
    assert "login failed" in result["error"]


def _async_ok(value):
    async def _f():
        return value
    return _f()


# ── setup status ───────────────────────────────────────────────────────────

def test_setup_status_reports_channels():
    with patch("admin.tools.organic.connect.get_active_token", return_value=None), \
         patch("admin.tools.organic.connect.get_channel_config", return_value={}):
        status = channel_setup_status("ws1")
    assert status["total"] >= 7
    assert status["connected_count"] == 0
    reddit = status["channels"]["reddit"]
    assert reddit["connected"] is False
    assert "client_secret" in reddit["missing"]
    assert reddit["fields"]


def test_setup_status_connected_when_creds_present():
    def fake_token(ws, platform):
        if platform in ("linkedin", "twitter", "pinterest", "gbp"):
            return {"access_token": "tok"}
        if platform == "reddit":
            return {"platform_user_id": "cid", "platform_username": "user"}
        if platform == "telegram":
            return {"access_token": "bot"}
        return None

    def fake_cfg(ws, channel):
        cfg = {
            "gbp": {"location_name": "accounts/1/locations/2"},
            "reddit": {"client_secret": "s", "password": "p"},
            "telegram": {"chat_id": "-100x"},
            "facebook": {"profile_dir": "/profiles/fb"},
        }
        return cfg.get(channel, {})

    with patch("admin.tools.organic.connect.get_active_token", side_effect=fake_token), \
         patch("admin.tools.organic.connect.get_channel_config", side_effect=fake_cfg):
        status = channel_setup_status("ws1")
    assert status["connected_count"] == status["total"]
    for cid, ch in status["channels"].items():
        assert ch["connected"] is True, f"{cid} not connected"
