# admin/tests/test_organic_oauth.py
"""Hermetic tests for the OAuth connect flow (admin/tools/organic/oauth.py).

Every test gets an isolated tmp data + token dir via a fixture that also
patches the module globals (oauth.OAUTH_DATA_DIR, token_manager._TOKENS_DIR)
so the full suite can't leak env state into these tests.
"""
from __future__ import annotations

import json
import os
from unittest.mock import patch

import pytest

import admin.token_manager as token_manager
from admin.tools.organic import oauth


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    data_dir = tmp_path / "organic_data"
    tok_dir = tmp_path / "tokens"
    monkeypatch.setenv("ORGANIC_DATA_DIR", str(data_dir))
    monkeypatch.setenv("TAGS_TOKENS_DIR", str(tok_dir))
    monkeypatch.setenv("OAUTH_REDIRECT_BASE", "https://test.example.com")
    monkeypatch.setenv("OAUTH_FRONTEND_URL", "https://test.example.com/admin/social")
    monkeypatch.setenv("OAUTH_LINKEDIN_CLIENT_ID", "linkedin_cid")
    monkeypatch.setenv("OAUTH_LINKEDIN_CLIENT_SECRET", "linkedin_csec")
    monkeypatch.setenv("OAUTH_TWITTER_CLIENT_ID", "tw_cid")
    monkeypatch.setenv("OAUTH_TWITTER_CLIENT_SECRET", "tw_csec")
    # Point module globals at the same isolated dirs (survives env churn).
    monkeypatch.setattr(oauth, "OAUTH_DATA_DIR", data_dir)
    monkeypatch.setattr(token_manager, "_TOKENS_DIR", tok_dir)
    oauth.OAUTH_DATA_DIR.mkdir(parents=True, exist_ok=True)
    return {"data_dir": data_dir, "tok_dir": tok_dir}


def _fake_post_response(payload: dict, ok: bool = True, status: int = 200):
    class _Resp:
        def __init__(self):
            self.ok = ok
            self.status_code = status
            self.text = json.dumps(payload)

        def json(self):
            return payload

    return _Resp()


def _token_file(isolated, channel: str) -> str:
    path = isolated["tok_dir"] / "ws1" / f"{channel}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path)


def _pending_dir(isolated) -> str:
    return str(isolated["data_dir"] / "ws1" / "oauth_pending")


# ── oauth_supported ─────────────────────────────────────────────────────────

def test_oauth_supported_channels():
    for ch in ("linkedin", "twitter", "pinterest", "reddit", "gbp"):
        assert oauth.oauth_supported(ch) is True
    for ch in ("telegram", "facebook"):
        assert oauth.oauth_supported(ch) is False


# ── build_auth_url ──────────────────────────────────────────────────────────

def test_build_auth_url_requires_credentials(isolated, monkeypatch):
    monkeypatch.delenv("OAUTH_PINTEREST_CLIENT_ID", raising=False)
    monkeypatch.delenv("OAUTH_PINTEREST_CLIENT_SECRET", raising=False)
    result = oauth.build_auth_url("ws1", "pinterest")
    assert result["status"] == "error"
    assert "No OAuth app configured" in result["error"]


def test_build_auth_url_unknown_channel(isolated):
    result = oauth.build_auth_url("ws1", "telegram")
    assert result["status"] == "error"
    assert "not supported" in result["error"]


def test_build_auth_url_linkedin(isolated):
    result = oauth.build_auth_url("ws1", "linkedin")
    assert result["status"] == "ok"
    url = result["auth_url"]
    assert result["channel"] == "linkedin"
    assert result["workspace_id"] == "ws1"
    assert "client_id=linkedin_cid" in url
    assert "redirect_uri=https%3A%2F%2Ftest.example.com%2Fapi%2Fsocial%2Foauth%2Fcallback" in url
    assert "response_type=code" in url
    assert "scope=w_member_social" in url
    assert "state=" in url
    state = result["state"]
    pending = json.load(open(os.path.join(_pending_dir(isolated), f"{state}.json"), encoding="utf-8"))
    assert pending["channel"] == "linkedin"
    assert pending["workspace_id"] == "ws1"


def test_build_auth_url_twitter_uses_pkce(isolated):
    result = oauth.build_auth_url("ws1", "twitter")
    assert result["status"] == "ok"
    assert "code_challenge=" in result["auth_url"]
    assert "code_challenge_method=S256" in result["auth_url"]
    state = result["state"]
    pending = json.load(open(os.path.join(_pending_dir(isolated), f"{state}.json"), encoding="utf-8"))
    assert pending["pkce_verifier"]


# ── app config (per-workspace creds) ────────────────────────────────────────

def test_save_and_status_app_config(isolated):
    # Pinterest has no env creds in the fixture, so the workspace file is used.
    result = oauth.save_app_config("ws2", "pinterest", {"client_id": "pcid", "client_secret": "pcsec"})
    assert result["status"] == "saved"
    status = oauth.app_config_status("ws2")
    assert status["channels"]["pinterest"]["configured"] is True
    assert status["channels"]["pinterest"]["source"] == "workspace"
    assert status["channels"]["linkedin"]["configured"] is True
    assert status["channels"]["linkedin"]["source"] == "env"


def test_save_app_config_invalid(isolated):
    result = oauth.save_app_config("ws2", "pinterest", {"client_id": ""})
    assert result["status"] == "error"
    result = oauth.save_app_config("ws2", "telegram", {"client_id": "x", "client_secret": "y"})
    assert result["status"] == "error"


# ── handle_callback ─────────────────────────────────────────────────────────

def test_callback_denied(isolated):
    result = oauth.handle_callback("linkedin", "nope", error="access_denied")
    assert result["status"] == "error"
    assert "access_denied" in result["error"]
    assert "success=0" in result["redirect"]


def test_callback_unknown_state(isolated):
    result = oauth.handle_callback("linkedin", "bogus-state", code="c1")
    assert result["status"] == "error"
    assert "unknown or expired" in result["error"]


def test_callback_happy_path_saves_token(isolated):
    start = oauth.build_auth_url("ws1", "linkedin")
    state = start["state"]

    def _fake_post(url, **kwargs):
        if "userinfo" in url:
            return _fake_post_response({"sub": "user-42", "name": "Ada Lovelace"})
        return _fake_post_response({
            "access_token": "acc123",
            "refresh_token": "ref123",
            "expires_in": 86400,
            "scope": "w_member_social",
        })

    with patch("admin.tools.organic.oauth.requests.post", side_effect=_fake_post) as mock_post:
        with patch("admin.tools.organic.oauth.requests.get", side_effect=_fake_post):
            result = oauth.handle_callback("linkedin", state, code="auth-code")

    assert result["status"] == "connected"
    assert result["user"] == "Ada Lovelace"
    assert "success=1" in result["redirect"]
    token = json.load(open(_token_file(isolated, "linkedin"), encoding="utf-8"))
    assert token["access_token"] == "acc123"
    assert token["refresh_token"] == "ref123"
    assert token["platform_user_id"] == "user-42"
    assert token["platform_username"] == "Ada Lovelace"
    assert token["expires_at"]
    assert "oauth" in token["token_type"]
    assert not os.path.exists(os.path.join(_pending_dir(isolated), f"{state}.json"))
    calls = [c for c in mock_post.call_args_list if "userinfo" not in str(c)]
    assert calls
    sent_data = calls[0].kwargs.get("data") or calls[0].args[0] or {}
    assert "auth-code" in str(sent_data)


# ── refresh ─────────────────────────────────────────────────────────────────

def test_refresh_access_token_happy(isolated):
    with open(_token_file(isolated, "twitter"), "w", encoding="utf-8") as f:
        json.dump({
            "platform": "twitter", "access_token": "old", "refresh_token": "ref_tw",
            "expires_at": "", "status": "active",
        }, f)

    with patch("admin.tools.organic.oauth.requests.post", return_value=_fake_post_response({
        "access_token": "new_tok", "refresh_token": "new_ref", "expires_in": 7200,
    })) as mock_post:
        result = oauth.refresh_access_token("ws1", "twitter")

    assert result["status"] == "refreshed"
    token = json.load(open(_token_file(isolated, "twitter"), encoding="utf-8"))
    assert token["access_token"] == "new_tok"
    assert token["refresh_token"] == "new_ref"
    assert token["expires_at"]
    sent = mock_post.call_args.kwargs.get("data", {})
    assert sent["grant_type"] == "refresh_token"
    assert sent["refresh_token"] == "ref_tw"
    assert mock_post.call_args.kwargs.get("auth") == ("tw_cid", "tw_csec")


def test_refresh_no_refresh_token(isolated):
    with open(_token_file(isolated, "pinterest"), "w", encoding="utf-8") as f:
        json.dump({"platform": "pinterest", "access_token": "x"}, f)
    result = oauth.refresh_access_token("ws1", "pinterest")
    assert result["status"] == "ok"  # long-lived channel, no refresh flow


def test_refresh_http_error(isolated):
    with open(_token_file(isolated, "linkedin"), "w", encoding="utf-8") as f:
        json.dump({"platform": "linkedin", "access_token": "x", "refresh_token": "r"}, f)
    with patch("admin.tools.organic.oauth.requests.post", return_value=_fake_post_response({}, ok=False, status=400)):
        result = oauth.refresh_access_token("ws1", "linkedin")
    assert result["status"] == "error"
    assert "400" in result["error"]


def test_ensure_fresh_token_skips_fresh(isolated):
    with open(_token_file(isolated, "linkedin"), "w", encoding="utf-8") as f:
        json.dump({
            "platform": "linkedin", "access_token": "x", "refresh_token": "r",
            "expires_at": "2099-01-01T00:00:00+00:00", "status": "active",
        }, f)
    with patch("admin.tools.organic.oauth.requests.post") as mock_post:
        result = oauth.ensure_fresh_token("ws1", "linkedin")
    assert result["status"] == "ok"
    assert result["reason"] == "fresh"
    mock_post.assert_not_called()


def test_ensure_fresh_token_refreshes_when_expired(isolated):
    with open(_token_file(isolated, "linkedin"), "w", encoding="utf-8") as f:
        json.dump({
            "platform": "linkedin", "access_token": "x", "refresh_token": "r",
            "expires_at": "2020-01-01T00:00:00+00:00", "status": "active",
        }, f)
    with patch("admin.tools.organic.oauth.requests.post", return_value=_fake_post_response({
        "access_token": "fresh", "refresh_token": "r2", "expires_in": 3600,
    })):
        result = oauth.ensure_fresh_token("ws1", "linkedin")
    assert result["status"] == "refreshed"
    token = json.load(open(_token_file(isolated, "linkedin"), encoding="utf-8"))
    assert token["access_token"] == "fresh"
