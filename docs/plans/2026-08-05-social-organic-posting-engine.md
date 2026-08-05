# Social Organic Posting Engine — Implementation Plan (Phase 1)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a modular organic posting engine so the Social Agent can post to Reddit, LinkedIn, X, Pinterest, Telegram, Google Business via API and Facebook Groups/Marketplace via browser automation, replacing the placeholder `post_now`/`schedule_post`.

**Architecture:** `admin/tools/organic/` package — `base.py` (models + validation), per-channel modules (raw `requests`, no new deps), `facebook_browser.py` (reuses ChromeTool), `registry.py` (channel catalog), `hub.py` (router). Wired into `social_tools.py`, `api/routes/social.py`, and the frontend social page. Superpower skill detection added via `admin/agency/social_skills.py` (mirrors `website_skills.py`).

**Tech Stack:** Python 3.11+, FastAPI, `requests` (already used across codebase), ChromeTool (Playwright/CDP browser automation, exists), token_manager (exists), Next.js frontend.

## Global Constraints

- **No new third-party dependencies** — all API modules use `requests` (already in requirements)
- Every public function returns a `dict` with a `status` key (`"published"`, `"queued"`, `"error"`, `"config_missing"`)
- Tokens always read via `admin.token_manager.get_active_token(workspace_id, platform)` — never hardcode
- Channel config (subreddits, chat IDs, group URLs) goes through `organic_config.py` — never hardcode
- All modules importable with no network (imports at function level for requests where possible)
- Browser work always goes through `admin.tools.chrome_tool.ChromeTool`
- Tests live in `admin/tests/`, use pytest
- No destructive changes to existing `social_tools.py` behavior — placeholder functions stay but now call the hub

---

### Task 1: organic package + base models

**Files:**
- Create: `admin/tools/organic/__init__.py`
- Create: `admin/tools/organic/base.py`
- Test: `admin/tests/test_organic_base.py`

**Interfaces:**
- Consumes: nothing
- Produces: `PostResult` dataclass (`status`, `channel`, `post_id`, `post_url`, `error`, `published_at`), `validate_payload(channel_meta, payload) -> list[str]` (returns missing-field errors), `CHANNEL_TYPE_API = "api"`, `CHANNEL_TYPE_BROWSER = "browser"`

- [ ] **Step 1: Write the failing test**

```python
# admin/tests/test_organic_base.py
from admin.tools.organic.base import PostResult, validate_payload

def test_post_result_defaults():
    r = PostResult(channel="reddit")
    assert r.status == "published"
    assert r.channel == "reddit"
    assert r.post_url == ""
    assert r.error == ""

def test_post_result_error():
    r = PostResult(channel="reddit", status="error", error="boom")
    assert r.status == "error"

def test_validate_payload_missing_required():
    meta = {"required_fields": ["subreddit", "title", "body"]}
    errors = validate_payload(meta, {"subreddit": "r/test"})
    assert "title" in errors
    assert "body" in errors

def test_validate_payload_ok():
    meta = {"required_fields": ["subreddit", "title", "body"]}
    errors = validate_payload(meta, {"subreddit": "r/test", "title": "t", "body": "b"})
    assert errors == []

def test_validate_payload_no_required():
    errors = validate_payload({}, {"anything": 1})
    assert errors == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd admin && python -m pytest tests/test_organic_base.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'admin.tools.organic'`

- [ ] **Step 3: Write minimal implementation**

```python
# admin/tools/organic/__init__.py
"""Organic social posting engine — API + browser channels."""
from admin.tools.organic.base import PostResult, validate_payload

__all__ = ["PostResult", "validate_payload"]
```

```python
# admin/tools/organic/base.py
"""Base models and validation for organic channel posting."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

CHANNEL_TYPE_API = "api"
CHANNEL_TYPE_BROWSER = "browser"


@dataclass
class PostResult:
    """Standard result returned by every organic channel module."""

    status: str = "published"  # published | queued | error | config_missing
    channel: str = ""
    post_id: str = ""
    post_url: str = ""
    error: str = ""
    published_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "channel": self.channel,
            "post_id": self.post_id,
            "post_url": self.post_url,
            "error": self.error,
            "published_at": self.published_at,
        }


def validate_payload(meta: dict, payload: dict) -> list[str]:
    """Return list of missing required fields from payload against channel meta."""
    missing = []
    for field_name in meta.get("required_fields", []):
        value = payload.get(field_name)
        if value is None or str(value).strip() == "":
            missing.append(field_name)
    return missing
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd admin && python -m pytest tests/test_organic_base.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add admin/tools/organic/__init__.py admin/tools/organic/base.py admin/tests/test_organic_base.py
git commit -m "feat(organic): base models and payload validation"
```

---

### Task 2: per-workspace channel config store

**Files:**
- Create: `admin/tools/organic/config.py`
- Test: `admin/tests/test_organic_config.py`

**Interfaces:**
- Consumes: nothing
- Produces: `get_channel_config(workspace_id, channel) -> dict`, `save_channel_config(workspace_id, channel, data) -> dict`, `list_channel_configs(workspace_id) -> dict`. Config file: `admin/organic_config/<workspace_id>/<channel>.json`

- [ ] **Step 1: Write the failing test**

```python
# admin/tests/test_organic_config.py
import tempfile
from pathlib import Path
from unittest.mock import patch

from admin.tools.organic import config as cfg


def test_save_and_get_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(cfg, "ORGANIC_CONFIG_DIR", tmp_path)
    cfg.save_channel_config("ws1", "reddit", {"subreddits": ["r/test"], "client_id": "abc"})
    data = cfg.get_channel_config("ws1", "reddit")
    assert data["subreddits"] == ["r/test"]
    assert data["client_id"] == "abc"


def test_get_missing_returns_empty(monkeypatch, tmp_path):
    monkeypatch.setattr(cfg, "ORGANIC_CONFIG_DIR", tmp_path)
    assert cfg.get_channel_config("ws1", "telegram") == {}


def test_list_configs(monkeypatch, tmp_path):
    monkeypatch.setattr(cfg, "ORGANIC_CONFIG_DIR", tmp_path)
    cfg.save_channel_config("ws1", "reddit", {"a": 1})
    cfg.save_channel_config("ws1", "telegram", {"b": 2})
    listed = cfg.list_channel_configs("ws1")
    assert "reddit" in listed
    assert "telegram" in listed
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd admin && python -m pytest tests/test_organic_config.py -v`
Expected: FAIL — import error or function missing

- [ ] **Step 3: Write minimal implementation**

```python
# admin/tools/organic/config.py
"""Per-workspace channel configuration store (subreddits, chat IDs, group URLs).

Files live in admin/organic_config/<workspace_id>/<channel>.json
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

ORGANIC_CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "organic_config"


def _channel_dir(workspace_id: str) -> Path:
    d = ORGANIC_CONFIG_DIR / workspace_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_channel_config(workspace_id: str, channel: str) -> dict:
    f = _channel_dir(workspace_id) / f"{channel}.json"
    if not f.exists():
        return {}
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_channel_config(workspace_id: str, channel: str, data: dict) -> dict:
    f = _channel_dir(workspace_id) / f"{channel}.json"
    f.write_text(json.dumps(data, indent=2), encoding="utf-8")
    logger.info("Saved %s config for workspace %s", channel, workspace_id)
    return {"status": "saved", "channel": channel, "workspace_id": workspace_id}


def list_channel_configs(workspace_id: str) -> dict:
    d = _channel_dir(workspace_id)
    out = {}
    for f in sorted(d.glob("*.json")):
        try:
            out[f.stem] = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd admin && python -m pytest tests/test_organic_config.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add admin/tools/organic/config.py admin/tests/test_organic_config.py
git commit -m "feat(organic): per-workspace channel config store"
```

---

### Task 3: channel registry

**Files:**
- Create: `admin/tools/organic/registry.py`
- Test: `admin/tests/test_organic_registry.py`

**Interfaces:**
- Consumes: Task 1 (`CHANNEL_TYPE_API`, `CHANNEL_TYPE_BROWSER`), Task 2 (`get_channel_config` not needed here)
- Produces: `CHANNELS: dict[str, dict]` — id → meta (`id`, `name`, `type`, `auth`, `capabilities`, `required_fields`, `description`), `list_channels() -> list[dict]`, `get_channel(channel_id) -> dict | None`

- [ ] **Step 1: Write the failing test**

```python
# admin/tests/test_organic_registry.py
from admin.tools.organic.registry import CHANNELS, get_channel, list_channels


def test_registry_has_all_phase1_channels():
    for ch in ["reddit", "linkedin", "twitter", "pinterest", "telegram", "gbp", "facebook"]:
        assert ch in CHANNELS, f"missing {ch}"


def test_channel_meta_fields():
    reddit = CHANNELS["reddit"]
    assert reddit["type"] == "api"
    assert "post" in reddit["capabilities"]
    assert "subreddit" in reddit["required_fields"]


def test_facebook_is_browser():
    assert CHANNELS["facebook"]["type"] == "browser"
    assert "groups" in CHANNELS["facebook"]["capabilities"]


def test_get_channel():
    assert get_channel("reddit")["id"] == "reddit"
    assert get_channel("nope") is None


def test_list_channels_returns_list():
    lst = list_channels()
    assert isinstance(lst, list)
    assert len(lst) >= 7
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd admin && python -m pytest tests/test_organic_registry.py -v`
Expected: FAIL — import error

- [ ] **Step 3: Write minimal implementation**

```python
# admin/tools/organic/registry.py
"""Channel registry — single source of truth for what each channel can do."""
from __future__ import annotations

from admin.tools.organic.base import CHANNEL_TYPE_API, CHANNEL_TYPE_BROWSER

CHANNELS: dict[str, dict] = {
    "reddit": {
        "id": "reddit",
        "name": "Reddit",
        "type": CHANNEL_TYPE_API,
        "auth": "token",
        "capabilities": ["post", "comment"],
        "required_fields": ["subreddit", "title", "body"],
        "description": "Post to subreddits and comment on threads (PRAW-style via requests OAuth2).",
    },
    "linkedin": {
        "id": "linkedin",
        "name": "LinkedIn",
        "type": CHANNEL_TYPE_API,
        "auth": "token",
        "capabilities": ["post"],
        "required_fields": ["text"],
        "description": "Share text/URL post to profile or company page.",
    },
    "twitter": {
        "id": "twitter",
        "name": "X / Twitter",
        "type": CHANNEL_TYPE_API,
        "auth": "token",
        "capabilities": ["post", "reply"],
        "required_fields": ["text"],
        "description": "Post tweet or reply via X API v2.",
    },
    "pinterest": {
        "id": "pinterest",
        "name": "Pinterest",
        "type": CHANNEL_TYPE_API,
        "auth": "token",
        "capabilities": ["post"],
        "required_fields": ["title", "image_url", "board_id"],
        "description": "Create a pin on a board.",
    },
    "telegram": {
        "id": "telegram",
        "name": "Telegram",
        "type": CHANNEL_TYPE_API,
        "auth": "token",
        "capabilities": ["post"],
        "required_fields": ["text"],
        "description": "Send message/photo to a bot channel or group.",
    },
    "gbp": {
        "id": "gbp",
        "name": "Google Business Profile",
        "type": CHANNEL_TYPE_API,
        "auth": "token",
        "capabilities": ["post"],
        "required_fields": ["summary"],
        "description": "Create a local business post (offer/event/update).",
    },
    "facebook": {
        "id": "facebook",
        "name": "Facebook",
        "type": CHANNEL_TYPE_BROWSER,
        "auth": "browser_session",
        "capabilities": ["groups", "marketplace"],
        "required_fields": ["target"],  # group URL or marketplace
        "description": "Post to Facebook Groups and Marketplace listings via browser automation.",
    },
}


def get_channel(channel_id: str) -> dict | None:
    return CHANNELS.get(channel_id)


def list_channels() -> list[dict]:
    return [dict(v) for v in CHANNELS.values()]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd admin && python -m pytest tests/test_organic_registry.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add admin/tools/organic/registry.py admin/tests/test_organic_registry.py
git commit -m "feat(organic): channel registry"
```

---

### Task 4: hub router

**Files:**
- Create: `admin/tools/organic/hub.py`
- Test: `admin/tests/test_organic_hub.py`

**Interfaces:**
- Consumes: Task 1 (`PostResult`, `validate_payload`), Task 3 (`get_channel`)
- Produces: `post(channel_id, workspace_id, payload) -> dict` (routes to module, returns `PostResult.to_dict()`), `CHANNEL_MODULES: dict[str, str]` (channel id → module import path). Each API module exposes `post(workspace_id: str, payload: dict) -> PostResult`.

- [ ] **Step 1: Write the failing test**

```python
# admin/tests/test_organic_hub.py
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
    fake_module = type("M", (), {"post": lambda ws, payload: PostResult(channel="reddit", status="published", post_url="https://reddit.com/x")})()
    mock_load.return_value = fake_module
    result = post("reddit", "ws1", {"subreddit": "r/test", "title": "t", "body": "b"})
    assert result["status"] == "published"
    assert result["post_url"] == "https://reddit.com/x"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd admin && python -m pytest tests/test_organic_hub.py -v`
Expected: FAIL — import error

- [ ] **Step 3: Write minimal implementation**

```python
# admin/tools/organic/hub.py
"""Central router for organic channel posting."""
from __future__ import annotations

import importlib
import logging
from typing import Any

from admin.tools.organic.base import PostResult, validate_payload
from admin.tools.organic.registry import get_channel

logger = logging.getLogger(__name__)

CHANNEL_MODULES: dict[str, str] = {
    "reddit": "admin.tools.organic.reddit_api",
    "linkedin": "admin.tools.organic.linkedin_api",
    "twitter": "admin.tools.organic.twitter_api",
    "pinterest": "admin.tools.organic.pinterest_api",
    "telegram": "admin.tools.organic.telegram_api",
    "gbp": "admin.tools.organic.gbp_api",
    "facebook": "admin.tools.organic.facebook_browser",
}


def _load_module(channel_id: str):
    module_path = CHANNEL_MODULES.get(channel_id)
    if not module_path:
        return None
    try:
        return importlib.import_module(module_path)
    except ImportError as e:
        logger.error("Failed to import %s: %s", module_path, e)
        return None


def post(channel_id: str, workspace_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Route a post to the right channel module and return a standard result dict."""
    meta = get_channel(channel_id)
    if meta is None:
        return PostResult(status="error", channel=channel_id, error=f"Unknown channel: {channel_id}").to_dict()

    missing = validate_payload(meta, payload)
    if missing:
        return PostResult(
            status="error", channel=channel_id,
            error=f"Missing required fields: {', '.join(missing)}",
        ).to_dict()

    module = _load_module(channel_id)
    if module is None:
        return PostResult(status="error", channel=channel_id, error=f"Module not available for channel: {channel_id}").to_dict()

    try:
        result = module.post(workspace_id, payload)
        if isinstance(result, PostResult):
            return result.to_dict()
        return result
    except Exception as e:
        logger.exception("organic post failed on %s", channel_id)
        return PostResult(status="error", channel=channel_id, error=str(e)[:300]).to_dict()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd admin && python -m pytest tests/test_organic_hub.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add admin/tools/organic/hub.py admin/tests/test_organic_hub.py
git commit -m "feat(organic): hub router"
```

---

### Task 5: Reddit API module

**Files:**
- Create: `admin/tools/organic/reddit_api.py`
- Test: `admin/tests/test_organic_reddit.py`

**Interfaces:**
- Consumes: Task 1 (`PostResult`, `CHANNEL_TYPE_API`), Task 2 (`get_channel_config`), `admin.token_manager.get_active_token`
- Produces: `post(workspace_id, payload) -> PostResult`, `CHANNEL_META` dict (registry mirrors it). Config: `client_id`, `client_secret`, `username`, `password` (stored via token_manager: client_id → `platform_user_id`, client_secret → `access_token`, username → `platform_username`; password + subreddits in channel config). Payload: `subreddit`, `title`, `body`, optional `flair`.

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd admin && python -m pytest tests/test_organic_reddit.py -v`
Expected: FAIL — import error

- [ ] **Step 3: Write minimal implementation**

```python
# admin/tools/organic/reddit_api.py
"""Reddit posting via OAuth2 script app (raw requests, no PRAW dependency)."""
from __future__ import annotations

import logging

import requests

from admin.tools.organic.base import CHANNEL_TYPE_API, PostResult
from admin.tools.organic.config import get_channel_config
from admin.token_manager import get_active_token

logger = logging.getLogger(__name__)

CHANNEL_META = {
    "id": "reddit",
    "name": "Reddit",
    "type": CHANNEL_TYPE_API,
    "auth": "token",
    "capabilities": ["post", "comment"],
    "required_fields": ["subreddit", "title", "body"],
    "description": "Post to subreddits and comment on threads.",
}

REDDIT_OAUTH_URL = "https://www.reddit.com/api/v1/access_token"
REDDIT_API_URL = "https://oauth.reddit.com"


def _get_access_token(client_id: str, client_secret: str, username: str, password: str) -> str | None:
    try:
        resp = requests.post(
            REDDIT_OAUTH_URL,
            auth=(client_id, client_secret),
            data={"grant_type": "password", "username": username, "password": password},
            headers={"User-Agent": "AgencyOrganicBot/1.0"},
            timeout=30,
        )
        if resp.ok:
            return resp.json().get("access_token")
        logger.error("Reddit auth failed: %s", resp.text[:200])
        return None
    except Exception as e:
        logger.error("Reddit auth error: %s", e)
        return None


def post(workspace_id: str, payload: dict) -> PostResult:
    token_data = get_active_token(workspace_id, "reddit")
    if not token_data:
        return PostResult(status="config_missing", channel="reddit", error="No Reddit token. Connect via /api/social/organic/config first.")

    cfg = get_channel_config(workspace_id, "reddit")
    client_id = token_data.get("platform_user_id") or cfg.get("client_id", "")
    client_secret = cfg.get("client_secret", "")
    username = token_data.get("platform_username") or cfg.get("username", "")
    password = cfg.get("password", "")

    if not (client_id and client_secret and username and password):
        return PostResult(status="config_missing", channel="reddit", error="Reddit creds incomplete (client_id, client_secret, username, password).")

    access_token = _get_access_token(client_id, client_secret, username, password)
    if not access_token:
        return PostResult(status="error", channel="reddit", error="Reddit auth failed. Check credentials.")

    subreddit = payload["subreddit"].lstrip("r/")
    data = {"sr": subreddit, "title": payload["title"], "kind": "self", "text": payload["body"]}
    if payload.get("flair"):
        data["flair_id"] = payload["flair"]

    try:
        resp = requests.post(
            f"{REDDIT_API_URL}/api/submit",
            headers={"Authorization": f"bearer {access_token}", "User-Agent": "AgencyOrganicBot/1.0"},
            data=data,
            timeout=30,
        )
        if resp.ok:
            j = resp.json()
            post_id = ""
            if j.get("json", {}).get("data", {}).get("id"):
                post_id = j["json"]["data"]["id"]
            return PostResult(
                channel="reddit",
                post_id=post_id,
                post_url=f"https://www.reddit.com/r/{subreddit}/comments/{post_id}" if post_id else "",
            )
        return PostResult(status="error", channel="reddit", error=resp.text[:300])
    except Exception as e:
        return PostResult(status="error", channel="reddit", error=str(e)[:300])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd admin && python -m pytest tests/test_organic_reddit.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add admin/tools/organic/reddit_api.py admin/tests/test_organic_reddit.py
git commit -m "feat(organic): Reddit API posting module"
```

---

### Task 6: Telegram API module

**Files:**
- Create: `admin/tools/organic/telegram_api.py`
- Test: `admin/tests/test_organic_telegram.py`

**Interfaces:**
- Consumes: Task 1, Task 2, token_manager
- Produces: `post(workspace_id, payload) -> PostResult`. Config: `bot_token` (or via token_manager `telegram.json` access_token), `chat_id` (config). Payload: `text`, optional `photo_url`, `link`.

- [ ] **Step 1: Write the failing test**

```python
# admin/tests/test_organic_telegram.py
from unittest.mock import patch

from admin.tools.organic.telegram_api import post


def test_post_no_config():
    with patch("admin.tools.organic.telegram_api.get_active_token", return_value=None):
        with patch("admin.tools.organic.telegram_api.get_channel_config", return_value={}):
            result = post("ws1", {"text": "hello"})
    assert result.status == "config_missing"


def test_post_ok():
    with patch("admin.tools.organic.telegram_api.get_active_token", return_value={"access_token": "bot123"}):
        with patch("admin.tools.organic.telegram_api.get_channel_config", return_value={"chat_id": "-100123"}):
            with patch("admin.tools.organic.telegram_api.requests.post") as mock_post:
                mock_post.return_value.ok = True
                mock_post.return_value.json.return_value = {"result": {"message_id": 42}}
                result = post("ws1", {"text": "hello"})
    assert result.status == "published"
    assert result.post_id == "42"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd admin && python -m pytest tests/test_organic_telegram.py -v`
Expected: FAIL — import error

- [ ] **Step 3: Write minimal implementation**

```python
# admin/tools/organic/telegram_api.py
"""Telegram posting via Bot API."""
from __future__ import annotations

import logging

import requests

from admin.tools.organic.base import CHANNEL_TYPE_API, PostResult
from admin.tools.organic.config import get_channel_config
from admin.token_manager import get_active_token

logger = logging.getLogger(__name__)

CHANNEL_META = {
    "id": "telegram",
    "name": "Telegram",
    "type": CHANNEL_TYPE_API,
    "auth": "token",
    "capabilities": ["post"],
    "required_fields": ["text"],
    "description": "Send message/photo to a bot channel or group.",
}


def post(workspace_id: str, payload: dict) -> PostResult:
    token_data = get_active_token(workspace_id, "telegram")
    bot_token = (token_data or {}).get("access_token", "")
    cfg = get_channel_config(workspace_id, "telegram")
    chat_id = cfg.get("chat_id", "")

    if not bot_token:
        return PostResult(status="config_missing", channel="telegram", error="No Telegram bot token.")
    if not chat_id:
        return PostResult(status="config_missing", channel="telegram", error="No chat_id in config.")

    try:
        base = f"https://api.telegram.org/bot{bot_token}"
        if payload.get("photo_url"):
            resp = requests.post(
                f"{base}/sendPhoto",
                data={"chat_id": chat_id, "caption": payload["text"]},
                files={"photo": requests.get(payload["photo_url"], timeout=30).content},
                timeout=60,
            )
        else:
            resp = requests.post(
                f"{base}/sendMessage",
                data={"chat_id": chat_id, "text": payload["text"], "disable_web_page_preview": False},
                timeout=30,
            )
        if resp.ok:
            j = resp.json()
            message_id = str(j.get("result", {}).get("message_id", ""))
            return PostResult(channel="telegram", post_id=message_id, post_url=f"https://t.me/c/{chat_id.replace('-100', '')}/{message_id}" if message_id else "")
        return PostResult(status="error", channel="telegram", error=resp.text[:300])
    except Exception as e:
        return PostResult(status="error", channel="telegram", error=str(e)[:300])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd admin && python -m pytest tests/test_organic_telegram.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add admin/tools/organic/telegram_api.py admin/tests/test_organic_telegram.py
git commit -m "feat(organic): Telegram API posting module"
```

---

### Task 7: X / Twitter API module

**Files:**
- Create: `admin/tools/organic/twitter_api.py`
- Test: `admin/tests/test_organic_twitter.py`

**Interfaces:**
- Consumes: Task 1, Task 2, token_manager
- Produces: `post(workspace_id, payload) -> PostResult`. Payload: `text`, optional `image_url`, `reply_to`. Token: `twitter.json` access_token (bearer or OAuth2 user token).

- [ ] **Step 1: Write the failing test**

```python
# admin/tests/test_organic_twitter.py
from unittest.mock import patch

from admin.tools.organic.twitter_api import post


def test_post_no_token():
    with patch("admin.tools.organic.twitter_api.get_active_token", return_value=None):
        result = post("ws1", {"text": "tweet"})
    assert result.status == "config_missing"


def test_post_ok():
    with patch("admin.tools.organic.twitter_api.get_active_token", return_value={"access_token": "bearer123"}):
        with patch("admin.tools.organic.twitter_api.requests.post") as mock_post:
            mock_post.return_value.ok = True
            mock_post.return_value.json.return_value = {"data": {"id": "987"}}
            result = post("ws1", {"text": "hello world"})
    assert result.status == "published"
    assert result.post_id == "987"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd admin && python -m pytest tests/test_organic_twitter.py -v`
Expected: FAIL — import error

- [ ] **Step 3: Write minimal implementation**

```python
# admin/tools/organic/twitter_api.py
"""X / Twitter posting via API v2."""
from __future__ import annotations

import logging

import requests

from admin.tools.organic.base import CHANNEL_TYPE_API, PostResult
from admin.token_manager import get_active_token

logger = logging.getLogger(__name__)

CHANNEL_META = {
    "id": "twitter",
    "name": "X / Twitter",
    "type": CHANNEL_TYPE_API,
    "auth": "token",
    "capabilities": ["post", "reply"],
    "required_fields": ["text"],
    "description": "Post tweet or reply via X API v2.",
}

TWITTER_API_URL = "https://api.twitter.com/2/tweets"


def post(workspace_id: str, payload: dict) -> PostResult:
    token_data = get_active_token(workspace_id, "twitter")
    if not token_data:
        return PostResult(status="config_missing", channel="twitter", error="No X/Twitter token.")
    token = token_data.get("access_token", "")
    if not token:
        return PostResult(status="config_missing", channel="twitter", error="Empty X/Twitter token.")

    body = {"text": payload["text"]}
    if payload.get("reply_to"):
        body["reply"] = {"in_reply_to_tweet_id": str(payload["reply_to"])}

    try:
        resp = requests.post(
            TWITTER_API_URL,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=body,
            timeout=30,
        )
        if resp.ok:
            tweet_id = resp.json().get("data", {}).get("id", "")
            return PostResult(channel="twitter", post_id=tweet_id, post_url=f"https://x.com/i/status/{tweet_id}" if tweet_id else "")
        return PostResult(status="error", channel="twitter", error=resp.text[:300])
    except Exception as e:
        return PostResult(status="error", channel="twitter", error=str(e)[:300])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd admin && python -m pytest tests/test_organic_twitter.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add admin/tools/organic/twitter_api.py admin/tests/test_organic_twitter.py
git commit -m "feat(organic): X/Twitter API posting module"
```

---

### Task 8: LinkedIn API module

**Files:**
- Create: `admin/tools/organic/linkedin_api.py`
- Test: `admin/tests/test_organic_linkedin.py`

**Interfaces:**
- Consumes: Task 1, token_manager
- Produces: `post(workspace_id, payload) -> PostResult`. Payload: `text`, optional `person_urn`/`company_urn` (default: use `platform_user_id`). Token: `linkedin.json` access_token.

- [ ] **Step 1: Write the failing test**

```python
# admin/tests/test_organic_linkedin.py
from unittest.mock import patch

from admin.tools.organic.linkedin_api import post


def test_post_no_token():
    with patch("admin.tools.organic.linkedin_api.get_active_token", return_value=None):
        result = post("ws1", {"text": "hi"})
    assert result.status == "config_missing"


def test_post_ok():
    with patch("admin.tools.organic.linkedin_api.get_active_token", return_value={"access_token": "li_token", "platform_user_id": "urn:li:person:abc"}):
        with patch("admin.tools.organic.linkedin_api.requests.post") as mock_post:
            mock_post.return_value.ok = True
            mock_post.return_value.json.return_value = {"id": "post123"}
            result = post("ws1", {"text": "hello linkedin"})
    assert result.status == "published"
    assert result.post_id == "post123"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd admin && python -m pytest tests/test_organic_linkedin.py -v`
Expected: FAIL — import error

- [ ] **Step 3: Write minimal implementation**

```python
# admin/tools/organic/linkedin_api.py
"""LinkedIn posting via REST API (UGC posts)."""
from __future__ import annotations

import logging

import requests

from admin.tools.organic.base import CHANNEL_TYPE_API, PostResult
from admin.token_manager import get_active_token

logger = logging.getLogger(__name__)

CHANNEL_META = {
    "id": "linkedin",
    "name": "LinkedIn",
    "type": CHANNEL_TYPE_API,
    "auth": "token",
    "capabilities": ["post"],
    "required_fields": ["text"],
    "description": "Share text post to profile or company page.",
}


def post(workspace_id: str, payload: dict) -> PostResult:
    token_data = get_active_token(workspace_id, "linkedin")
    if not token_data:
        return PostResult(status="config_missing", channel="linkedin", error="No LinkedIn token.")
    token = token_data.get("access_token", "")
    author_urn = payload.get("person_urn") or token_data.get("platform_user_id", "")
    if not token:
        return PostResult(status="config_missing", channel="linkedin", error="Empty LinkedIn token.")
    if not author_urn:
        return PostResult(status="config_missing", channel="linkedin", error="No author URN. Connect with LinkedIn and store platform_user_id.")

    body = {
        "author": f"urn:li:person:{author_urn}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": payload["text"]},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }

    try:
        resp = requests.post(
            "https://api.linkedin.com/v2/ugcPosts",
            headers={"Authorization": f"Bearer {token}", "X-Restli-Protocol-Version": "2.0.0", "Content-Type": "application/json"},
            json=body,
            timeout=30,
        )
        if resp.ok:
            post_id = resp.json().get("id", "")
            return PostResult(channel="linkedin", post_id=post_id)
        return PostResult(status="error", channel="linkedin", error=resp.text[:300])
    except Exception as e:
        return PostResult(status="error", channel="linkedin", error=str(e)[:300])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd admin && python -m pytest tests/test_organic_linkedin.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add admin/tools/organic/linkedin_api.py admin/tests/test_organic_linkedin.py
git commit -m "feat(organic): LinkedIn API posting module"
```

---

### Task 9: Pinterest API module

**Files:**
- Create: `admin/tools/organic/pinterest_api.py`
- Test: `admin/tests/test_organic_pinterest.py`

**Interfaces:**
- Consumes: Task 1, token_manager
- Produces: `post(workspace_id, payload) -> PostResult`. Payload: `title`, `description`, `image_url`, `link`, `board_id`. Token: `pinterest.json` access_token.

- [ ] **Step 1: Write the failing test**

```python
# admin/tests/test_organic_pinterest.py
from unittest.mock import patch

from admin.tools.organic.pinterest_api import post


def test_post_no_token():
    with patch("admin.tools.organic.pinterest_api.get_active_token", return_value=None):
        result = post("ws1", {"title": "t", "image_url": "https://x/y.jpg", "board_id": "b"})
    assert result.status == "config_missing"


def test_post_ok():
    with patch("admin.tools.organic.pinterest_api.get_active_token", return_value={"access_token": "pin_token"}):
        with patch("admin.tools.organic.pinterest_api.requests.post") as mock_post:
            mock_post.return_value.ok = True
            mock_post.return_value.json.return_value = {"id": "pin123"}
            result = post("ws1", {"title": "t", "description": "d", "image_url": "https://x/y.jpg", "link": "https://shop/x", "board_id": "b1"})
    assert result.status == "published"
    assert result.post_id == "pin123"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd admin && python -m pytest tests/test_organic_pinterest.py -v`
Expected: FAIL — import error

- [ ] **Step 3: Write minimal implementation**

```python
# admin/tools/organic/pinterest_api.py
"""Pinterest pin creation via REST API."""
from __future__ import annotations

import logging

import requests

from admin.tools.organic.base import CHANNEL_TYPE_API, PostResult
from admin.token_manager import get_active_token

logger = logging.getLogger(__name__)

CHANNEL_META = {
    "id": "pinterest",
    "name": "Pinterest",
    "type": CHANNEL_TYPE_API,
    "auth": "token",
    "capabilities": ["post"],
    "required_fields": ["title", "image_url", "board_id"],
    "description": "Create a pin on a board.",
}


def post(workspace_id: str, payload: dict) -> PostResult:
    token_data = get_active_token(workspace_id, "pinterest")
    if not token_data:
        return PostResult(status="config_missing", channel="pinterest", error="No Pinterest token.")
    token = token_data.get("access_token", "")
    if not token:
        return PostResult(status="config_missing", channel="pinterest", error="Empty Pinterest token.")

    body = {
        "board_id": payload["board_id"],
        "media_source": {"source_type": "image_url", "url": payload["image_url"]},
        "title": payload.get("title", ""),
        "description": payload.get("description", payload.get("title", "")),
        "link": payload.get("link", ""),
    }

    try:
        resp = requests.post(
            "https://api-sandbox.pinterest.com/v5/pins",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=body,
            timeout=30,
        )
        if resp.ok:
            pin_id = resp.json().get("id", "")
            return PostResult(channel="pinterest", post_id=pin_id, post_url=f"https://www.pinterest.com/pin/{pin_id}" if pin_id else "")
        return PostResult(status="error", channel="pinterest", error=resp.text[:300])
    except Exception as e:
        return PostResult(status="error", channel="pinterest", error=str(e)[:300])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd admin && python -m pytest tests/test_organic_pinterest.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add admin/tools/organic/pinterest_api.py admin/tests/test_organic_pinterest.py
git commit -m "feat(organic): Pinterest API posting module"
```

---

### Task 10: Google Business Profile module

**Files:**
- Create: `admin/tools/organic/gbp_api.py`
- Test: `admin/tests/test_organic_gbp.py`

**Interfaces:**
- Consumes: Task 1, token_manager
- Produces: `post(workspace_id, payload) -> PostResult`. Payload: `summary`, optional `offer`, `event`, `topic_type`. Token: `gbp.json` access_token + config `location_name`/`account_id`.

- [ ] **Step 1: Write the failing test**

```python
# admin/tests/test_organic_gbp.py
from unittest.mock import patch

from admin.tools.organic.gbp_api import post


def test_post_no_token():
    with patch("admin.tools.organic.gbp_api.get_active_token", return_value=None):
        result = post("ws1", {"summary": "s"})
    assert result.status == "config_missing"


def test_post_ok():
    with patch("admin.tools.organic.gbp_api.get_active_token", return_value={"access_token": "gbp_tok"}):
        with patch("admin.tools.organic.gbp_api.requests.post") as mock_post:
            mock_post.return_value.ok = True
            mock_post.return_value.json.return_value = {"name": "accounts/1/locations/2/localPosts/3"}
            result = post("ws1", {"summary": "hello gbp"})
    assert result.status == "published"
    assert result.post_id == "accounts/1/locations/2/localPosts/3"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd admin && python -m pytest tests/test_organic_gbp.py -v`
Expected: FAIL — import error

- [ ] **Step 3: Write minimal implementation**

```python
# admin/tools/organic/gbp_api.py
"""Google Business Profile local post creation."""
from __future__ import annotations

import logging

import requests

from admin.tools.organic.base import CHANNEL_TYPE_API, PostResult
from admin.tools.organic.config import get_channel_config
from admin.token_manager import get_active_token

logger = logging.getLogger(__name__)

CHANNEL_META = {
    "id": "gbp",
    "name": "Google Business Profile",
    "type": CHANNEL_TYPE_API,
    "auth": "token",
    "capabilities": ["post"],
    "required_fields": ["summary"],
    "description": "Create a local business post (offer/event/update).",
}


def post(workspace_id: str, payload: dict) -> PostResult:
    token_data = get_active_token(workspace_id, "gbp")
    if not token_data:
        return PostResult(status="config_missing", channel="gbp", error="No GBP token.")
    token = token_data.get("access_token", "")
    cfg = get_channel_config(workspace_id, "gbp")
    location_name = payload.get("location_name") or cfg.get("location_name", "")
    if not token:
        return PostResult(status="config_missing", channel="gbp", error="Empty GBP token.")
    if not location_name:
        return PostResult(status="config_missing", channel="gbp", error="No location_name. Set it in channel config.")

    body = {
        "summary": payload["summary"],
        "callToAction": {"actionType": "LEARN_MORE", "url": payload.get("link", "")} if payload.get("link") else None,
        "topicType": payload.get("topic_type", "STANDARD"),
    }
    body = {k: v for k, v in body.items() if v is not None}

    try:
        resp = requests.post(
            f"https://mybusiness.googleapis.com/v4/{location_name}/localPosts",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=body,
            timeout=30,
        )
        if resp.ok:
            post_name = resp.json().get("name", "")
            return PostResult(channel="gbp", post_id=post_name)
        return PostResult(status="error", channel="gbp", error=resp.text[:300])
    except Exception as e:
        return PostResult(status="error", channel="gbp", error=str(e)[:300])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd admin && python -m pytest tests/test_organic_gbp.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add admin/tools/organic/gbp_api.py admin/tests/test_organic_gbp.py
git commit -m "feat(organic): Google Business Profile posting module"
```

---

### Task 11: Facebook browser module (Groups + Marketplace)

**Files:**
- Create: `admin/tools/organic/facebook_browser.py`
- Test: `admin/tests/test_organic_facebook.py`

**Interfaces:**
- Consumes: Task 1, Task 2 (`get_channel_config`), `admin.tools.chrome_tool.ChromeTool`
- Produces: `post(workspace_id, payload) -> PostResult`, `CHANNEL_META`. Config: `profile_dir` (Chrome profile with logged-in FB session), `default_groups` (list of group URLs). Payload: `target` (group URL or `"marketplace"`), `message`, optional `image_url`, `price`/`title` (for marketplace).

- [ ] **Step 1: Write the failing test**

```python
# admin/tests/test_organic_facebook.py
from unittest.mock import AsyncMock, patch

from admin.tools.organic.facebook_browser import post, _is_marketplace


def test_is_marketplace():
    assert _is_marketplace("marketplace") is True
    assert _is_marketplace("https://www.facebook.com/groups/123") is False


def test_post_requires_browser_config():
    with patch("admin.tools.organic.facebook_browser.get_channel_config", return_value={}):
        result = post("ws1", {"target": "https://www.facebook.com/groups/123", "message": "hi"})
    assert result.status == "config_missing"
    assert "profile_dir" in result.error


def test_post_marketplace_missing_fields():
    with patch("admin.tools.organic.facebook_browser.get_channel_config", return_value={"profile_dir": "x"}):
        result = post("ws1", {"target": "marketplace", "message": "hi"})
    assert result.status == "error"
    assert "price" in result.error
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd admin && python -m pytest tests/test_organic_facebook.py -v`
Expected: FAIL — import error

- [ ] **Step 3: Write minimal implementation**

```python
# admin/tools/organic/facebook_browser.py
"""Facebook Groups + Marketplace posting via ChromeTool browser automation.

Requires a saved Chrome profile where the client is already logged into
Facebook (profile_dir in channel config). All browser actions reuse
ChromeTool's stealth delays to look human.
"""
from __future__ import annotations

import logging

from admin.tools.organic.base import CHANNEL_TYPE_BROWSER, PostResult
from admin.tools.organic.config import get_channel_config

logger = logging.getLogger(__name__)

CHANNEL_META = {
    "id": "facebook",
    "name": "Facebook",
    "type": CHANNEL_TYPE_BROWSER,
    "auth": "browser_session",
    "capabilities": ["groups", "marketplace"],
    "required_fields": ["target"],
    "description": "Post to Facebook Groups and Marketplace listings via browser automation.",
}


def _is_marketplace(target: str) -> bool:
    return target.strip().lower() == "marketplace"


def post(workspace_id: str, payload: dict) -> PostResult:
    cfg = get_channel_config(workspace_id, "facebook")
    profile_dir = cfg.get("profile_dir", "")
    if not profile_dir:
        return PostResult(status="config_missing", channel="facebook", error="No profile_dir in config. Set a Chrome profile logged into Facebook.")

    target = payload.get("target", "")
    if _is_marketplace(target):
        if not payload.get("price"):
            return PostResult(status="error", channel="facebook", error="Marketplace listing needs 'price' (and 'title').")
    else:
        if "facebook.com/groups/" not in target:
            return PostResult(status="error", channel="facebook", error="target must be a facebook group URL or 'marketplace'.")

    # Deferred: browser flow implemented in Phase 1b once a real session is
    # available for testing. Returns queued so pipeline keeps moving.
    return PostResult(
        status="queued",
        channel="facebook",
        post_id="",
        post_url=target,
        error="",
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd admin && python -m pytest tests/test_organic_facebook.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add admin/tools/organic/facebook_browser.py admin/tests/test_organic_facebook.py
git commit -m "feat(organic): Facebook browser module (queued until live session)"
```

**Note on Phase 1b:** The full ChromeTool browser flow for FB Groups/Marketplace (goto → click post box → fill → submit, with screenshot verification) lands as a follow-up task after the engine is wired, because it needs a real logged-in profile to develop against. The `queued` status keeps the contract stable meanwhile.

---

### Task 12: Wire organic engine into social_tools

**Files:**
- Modify: `admin/tools/social_tools.py` (add `organic_post` + `organic_channels` functions; replace `post_now`/`schedule_post` placeholders)
- Test: `admin/tests/test_organic_wiring.py`

**Interfaces:**
- Consumes: Task 4 (`admin.tools.organic.hub.post`), Task 3 (`list_channels`), Task 2 (`save_channel_config`, `list_channel_configs`, `get_channel_config`)
- Produces: `organic_post(channel, workspace_id, payload) -> dict`, `organic_channels(workspace_id) -> dict`, `organic_save_config(channel, workspace_id, config) -> dict`. `post_now`/`schedule_post` now delegate to `organic_post` when a `channel` key is present in `post_data`, else keep old behavior.

- [ ] **Step 1: Write the failing test**

```python
# admin/tests/test_organic_wiring.py
from unittest.mock import patch

from admin.tools.social_tools import organic_post, organic_channels, post_now


def test_organic_post_routes():
    with patch("admin.tools.social_tools._organic_hub") as mock_hub_loader:
        mock_hub_loader.return_value = lambda channel, ws, payload: {"status": "published", "channel": channel}
        result = organic_post("reddit", "ws1", {"subreddit": "r/test", "title": "t", "body": "b"})
    assert result["status"] == "published"


def test_organic_channels_lists_registry():
    with patch("admin.tools.social_tools._organic_registry", return_value=[{"id": "reddit"}]):
        with patch("admin.tools.social_tools._organic_config") as mock_cfg:
            mock_cfg.return_value = (lambda *a, **k: {}, lambda ws: {"reddit": {"subreddits": ["r/test"]}}, lambda *a, **k: {})
            result = organic_channels("ws1")
    assert "channels" in result
    assert "configs" in result


def test_post_now_with_channel_delegates():
    with patch("admin.tools.social_tools.organic_post", return_value={"status": "published", "channel": "telegram"}) as mock_organic:
        result = post_now({"channel": "telegram", "workspace_id": "ws1", "text": "hi"})
    assert mock_organic.called
    assert result["status"] == "published"


def test_post_now_without_channel_keeps_behavior():
    result = post_now({"platform": "instagram", "caption": "x"})
    assert result["status"] == "published"
    assert "post_data" in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd admin && python -m pytest tests/test_organic_wiring.py -v`
Expected: FAIL — `organic_post` not defined

- [ ] **Step 3: Write minimal implementation**

Add at the top of `admin/tools/social_tools.py` (after existing imports):

```python
# ── Organic engine imports (lazy, so social_tools stays importable standalone) ──
def _organic_hub():
    from admin.tools.organic.hub import post as hub_post
    return hub_post


def _organic_registry():
    from admin.tools.organic.registry import list_channels
    return list_channels()


def _organic_config():
    from admin.tools.organic.config import get_channel_config, list_channel_configs, save_channel_config
    return get_channel_config, list_channel_configs, save_channel_config
```

Replace `post_now` (lines 633-639) with:

```python
def organic_post(channel: str, workspace_id: str, payload: dict) -> dict[str, Any]:
    """Post to an organic channel (reddit, telegram, twitter, linkedin, pinterest, gbp, facebook)."""
    hub_post = _organic_hub()
    return hub_post(channel, workspace_id, payload)


def organic_channels(workspace_id: str = "default") -> dict[str, Any]:
    """List available organic channels + their configs for a workspace."""
    channels = _organic_registry()
    _, list_configs, _ = _organic_config()
    return {"channels": channels, "configs": list_configs(workspace_id)}


def organic_save_config(channel: str, workspace_id: str, config: dict) -> dict[str, Any]:
    """Save per-workspace config for an organic channel (subreddits, chat_id, profile_dir...)."""
    _, _, save_config = _organic_config()
    return save_config(workspace_id, channel, config)


def post_now(post_data: dict[str, Any] | None = None) -> dict[str, Any]:
    """Post immediately. If post_data contains 'channel', route through organic engine."""
    post_data = post_data or {}
    if post_data.get("channel"):
        return organic_post(
            post_data["channel"],
            post_data.get("workspace_id", "default"),
            {k: v for k, v in post_data.items() if k not in ("channel", "workspace_id")},
        )
    return {
        "status": "published",
        "post_data": post_data,
        "published_at": datetime.now().isoformat(),
    }
```

Replace `schedule_post` (lines 623-630) with:

```python
def schedule_post(post_data: dict[str, Any] | None = None, datetime_str: str = "") -> dict[str, Any]:
    """Schedule a post. If post_data contains 'channel', queue through organic engine (Phase 3 scheduler)."""
    post_data = post_data or {}
    if post_data.get("channel"):
        return {
            "status": "queued",
            "scheduled_for": datetime_str,
            "channel": post_data["channel"],
            "workspace_id": post_data.get("workspace_id", "default"),
            "note": "Phase 3 scheduler will dispatch this at the scheduled time",
        }
    return {
        "status": "scheduled",
        "scheduled_for": datetime_str,
        "post_data": post_data,
        "note": "Production mein SocialClaw API call hoga",
    }
```

Add to `_TOOL_REGISTRY`:

```python
    "organic_post": organic_post,
    "organic_channels": organic_channels,
    "organic_save_config": organic_save_config,
```

And register the functions in `SOCIAL_TOOLS` list (append three entries):

```python
    {"type": "function", "function": {"name": "organic_post", "description": "Post to organic channels (reddit, telegram, twitter, linkedin, pinterest, gbp, facebook)", "parameters": {"type": "object", "properties": {"channel": {"type": "string"}, "workspace_id": {"type": "string"}, "payload": {"type": "object"}}}}},
    {"type": "function", "function": {"name": "organic_channels", "description": "List organic channels and their configs", "parameters": {"type": "object", "properties": {"workspace_id": {"type": "string"}}}}},
    {"type": "function", "function": {"name": "organic_save_config", "description": "Save channel config (subreddits, chat_id, profile_dir)", "parameters": {"type": "object", "properties": {"channel": {"type": "string"}, "workspace_id": {"type": "string"}, "config": {"type": "object"}}}}},
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd admin && python -m pytest tests/test_organic_wiring.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Run existing social tests to ensure nothing broke**

Run: `cd admin && python -m pytest tests/test_api_endpoints.py -k social -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add admin/tools/social_tools.py admin/tests/test_organic_wiring.py
git commit -m "feat(social): wire organic posting engine into social tools"
```

---

### Task 13: API routes for organic engine

**Files:**
- Modify: `admin/api/routes/social.py` (add routes + request models)
- Test: `admin/tests/test_organic_routes.py`

**Interfaces:**
- Consumes: Task 12 (`organic_post`, `organic_channels`, `organic_save_config`)
- Produces: `POST /api/social/organic/post`, `GET /api/social/organic/channels`, `POST /api/social/organic/config`

- [ ] **Step 1: Write the failing test**

```python
# admin/tests/test_organic_routes.py
from fastapi.testclient import TestClient

from admin.main import app

client = TestClient(app)


def test_organic_channels_route():
    resp = client.get("/api/social/organic/channels?workspace_id=default")
    assert resp.status_code == 200
    data = resp.json()
    assert "channels" in data
    assert any(c["id"] == "reddit" for c in data["channels"])


def test_organic_post_route_unknown_channel():
    resp = client.post("/api/social/organic/post", json={"channel": "nope", "workspace_id": "default", "payload": {}})
    assert resp.status_code == 200
    assert resp.json()["status"] == "error"


def test_organic_save_config_route():
    resp = client.post("/api/social/organic/config", json={"channel": "telegram", "workspace_id": "ws_test", "config": {"chat_id": "-100abc"}})
    assert resp.status_code == 200
    assert resp.json()["status"] == "saved"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd admin && python -m pytest tests/test_organic_routes.py -v`
Expected: FAIL — 404 (routes missing)

- [ ] **Step 3: Write minimal implementation**

Add request models to `admin/api/routes/social.py` (after `TokenExchangeRequest`):

```python
class OrganicPostRequest(BaseModel):
    channel: str
    workspace_id: str = "default"
    payload: dict = {}


class OrganicConfigRequest(BaseModel):
    channel: str
    workspace_id: str = "default"
    config: dict = {}
```

Add endpoints (before `@router.get("/tools")`):

```python
@router.get("/organic/channels")
async def organic_channels_route(workspace_id: str = "default"):
    """List available organic channels + configs."""
    from admin.tools.social_tools import organic_channels
    return organic_channels(workspace_id)


@router.post("/organic/post")
async def organic_post_route(req: OrganicPostRequest):
    """Post to an organic channel."""
    from admin.tools.social_tools import organic_post
    return organic_post(req.channel, req.workspace_id, req.payload)


@router.post("/organic/config")
async def organic_config_route(req: OrganicConfigRequest):
    """Save channel config for a workspace."""
    from admin.tools.social_tools import organic_save_config
    return organic_save_config(req.channel, req.workspace_id, req.config)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd admin && python -m pytest tests/test_organic_routes.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add admin/api/routes/social.py admin/tests/test_organic_routes.py
git commit -m "feat(social): organic engine API routes"
```

---

### Task 14: social skills integration (superpower skills)

**Files:**
- Create: `admin/agency/social_skills.py`
- Modify: `admin/workspace/agents/social.py` (detect skills in chat, pass as context)
- Test: `admin/tests/test_social_skills.py`

**Interfaces:**
- Consumes: mirrors `admin/agency/website_skills.py` (skill dirs: `~/.jcode/skills`, `~/.agents/skills`)
- Produces: `SOCIAL_SKILL_REGISTRY: list[dict]`, `detect_skills(message, max_skills=2) -> list[dict]`, `build_skill_context(skills) -> str`, `list_social_skills() -> list[dict]`

- [ ] **Step 1: Write the failing test**

```python
# admin/tests/test_social_skills.py
from admin.agency.social_skills import SOCIAL_SKILL_REGISTRY, detect_skills, build_skill_context, list_social_skills


def test_registry_has_social_skills():
    names = [s["name"] for s in SOCIAL_SKILL_REGISTRY]
    assert "ad-creative" in names
    assert "social" in names
    assert "content-engine" in names


def test_detect_skills_finds_ad_creative():
    hits = detect_skills("make me ad copy variations for facebook ads", max_skills=2)
    names = [h["name"] for h in hits]
    assert "ad-creative" in names


def test_detect_skills_finds_social():
    hits = detect_skills("what should I post on linkedin this week")
    names = [h["name"] for h in hits]
    assert "social" in names


def test_build_skill_context_returns_string():
    ctx = build_skill_context([{"name": "social", "description": "d"}])
    assert isinstance(ctx, str)
    assert "social" in ctx


def test_list_social_skills():
    assert len(list_social_skills()) >= 3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd admin && python -m pytest tests/test_social_skills.py -v`
Expected: FAIL — import error

- [ ] **Step 3: Write minimal implementation**

```python
# admin/agency/social_skills.py
"""Social Agent Skills — loaded from Jcode's skill catalog.

Mirrors sba_skills.py / seo_skills.py / website_skills.py. Relevant skills
are auto-detected from the message and passed as context so the Social
Agent can apply real marketing, copywriting, and content frameworks.
"""
from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

JCODE_SKILLS_DIR = Path.home() / ".jcode" / "skills"
AGENTS_SKILLS_DIR = Path.home() / ".agents" / "skills"

SOCIAL_SKILL_REGISTRY: list[dict] = [
    {
        "name": "ad-creative",
        "keywords": [
            "ad copy", "ad creative", "headline", "rsa", "facebook ad",
            "google ad", "ad variations", "hook writing", "creative strategy",
        ],
        "description": "Generate and iterate paid ad creative (headlines, descriptions, primary text)",
    },
    {
        "name": "social",
        "keywords": [
            "linkedin post", "twitter thread", "instagram", "social media",
            "content calendar", "viral", "what should i post", "reel", "carousel",
            "caption", "post ideas", "social strategy", "hashtag",
        ],
        "description": "Social media content creation, scheduling, and strategy",
    },
    {
        "name": "content-engine",
        "keywords": [
            "content system", "content plan", "repurpose", "multi-platform",
            "content pipeline", "newsletter", "youtube script",
        ],
        "description": "Platform-native content systems and repurposing",
    },
    {
        "name": "post-writer-sms",
        "keywords": [
            "write a post", "post for me", "draft post", "engagement post",
            "cta post", "announcement post",
        ],
        "description": "Write platform-native social posts",
    },
    {
        "name": "brand-voice",
        "keywords": [
            "brand voice", "tone of voice", "writing style", "voice profile",
            "consistent voice", "copy style",
        ],
        "description": "Build a source-derived writing style profile",
    },
    {
        "name": "content-calendar-sms",
        "keywords": [
            "content calendar", "posting schedule", "when to post",
            "content cadence", "weekly plan", "monthly content plan",
        ],
        "description": "Plan social media posting schedules and calendars",
    },
]

MAX_SKILL_CONTENT_CHARS = 2000
MAX_TOTAL_SKILL_CHARS = 4000


def _load_skill_content(skill_name: str) -> str | None:
    for base in (JCODE_SKILLS_DIR, AGENTS_SKILLS_DIR):
        f = base / skill_name / "SKILL.md"
        if f.exists():
            try:
                return f.read_text(encoding="utf-8", errors="ignore")[:MAX_SKILL_CONTENT_CHARS]
            except OSError:
                continue
    return None


def detect_skills(message: str, max_skills: int = 2) -> list[dict]:
    msg_lower = message.lower()
    hits = []
    for skill in SOCIAL_SKILL_REGISTRY:
        if any(kw in msg_lower for kw in skill["keywords"]):
            content = _load_skill_content(skill["name"])
            if content:
                hits.append({**skill, "content": content})
            else:
                hits.append({**skill, "content": ""})
        if len(hits) >= max_skills:
            break
    return hits


def build_skill_context(skills: list[dict]) -> str:
    parts = []
    total = 0
    for s in skills:
        content = s.get("content", "")
        if not content:
            continue
        block = f"### {s['name']}\n{content}"
        if total + len(block) > MAX_TOTAL_SKILL_CHARS:
            block = block[: MAX_TOTAL_SKILL_CHARS - total]
        parts.append(block)
        total += len(block)
        if total >= MAX_TOTAL_SKILL_CHARS:
            break
    return "\n\n".join(parts)


def list_social_skills() -> list[dict]:
    out = []
    for s in SOCIAL_SKILL_REGISTRY:
        out.append({"name": s["name"], "description": s["description"], "keywords": s["keywords"]})
    return out
```

Wire into `admin/workspace/agents/social.py` chat flow:

Find the chat method (it calls the LLM with the system prompt). Add skill detection before the LLM call:

```python
from admin.agency.social_skills import detect_skills, build_skill_context
```

And in the chat method, before building the LLM messages:

```python
        # Superpower skill context injection
        skills = detect_skills(user_message)
        skill_ctx = build_skill_context(skills)
        if skill_ctx:
            messages[-1]["content"] += (
                "\n\n## Relevant Skills (use these frameworks)\n" + skill_ctx
            )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd admin && python -m pytest tests/test_social_skills.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add admin/agency/social_skills.py admin/workspace/agents/social.py admin/tests/test_social_skills.py
git commit -m "feat(social): superpower skill detection in Social Agent chat"
```

---

### Task 15: frontend organic panel

**Files:**
- Modify: `agency-frontend/src/app/admin/social/page.js` (add Organic Channels section)
- Test: manual — `cd agency-frontend && npm run build`

**Interfaces:**
- Consumes: `GET /api/social/organic/channels`, `POST /api/social/organic/post`, `POST /api/social/organic/config` (proxied same-origin like other API calls in this file)

- [ ] **Step 1: Add the Organic Channels panel**

Add a section to `page.js` (follow the existing component style in that file — it already fetches `/api/social/*`). The panel should:

1. On mount, `GET /api/social/organic/channels?workspace_id=default` → render channel cards (id, name, type, capabilities, auth) + per-channel config JSON (editable textarea) + "Save config" button → `POST /api/social/organic/config`
2. A "Post" composer: select channel (dropdown from channels), textarea for JSON payload (with a template per channel: reddit `{"subreddit","title","body"}`, telegram `{"text"}`, twitter `{"text"}`, linkedin `{"text"}`, pinterest `{"title","image_url","board_id"}`, gbp `{"summary"}`, facebook `{"target","message"}`), and a "Post Now" button → `POST /api/social/organic/post`
3. Show result status + error inline.

Implementation sketch (paste into the file, adapting to existing imports/style):

```jsx
// Organic Channels state
const [organicChannels, setOrganicChannels] = useState([]);
const [organicConfigs, setOrganicConfigs] = useState({});
const [configDraft, setConfigDraft] = useState("{}");
const [postChannel, setPostChannel] = useState("reddit");
const [postPayload, setPostPayload] = useState(JSON.stringify({ subreddit: "r/test", title: "", body: "" }, null, 2));
const [postResult, setPostResult] = useState(null);

useEffect(() => {
  fetch("/api/social/organic/channels?workspace_id=default")
    .then((r) => r.json())
    .then((d) => { setOrganicChannels(d.channels || []); setOrganicConfigs(d.configs || {}); })
    .catch(() => {});
}, []);

async function saveOrganicConfig() {
  const res = await fetch("/api/social/organic/config", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ channel: postChannel, workspace_id: "default", config: JSON.parse(configDraft) }),
  });
  setPostResult(await res.json());
}

async function organicPostNow() {
  const res = await fetch("/api/social/organic/post", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ channel: postChannel, workspace_id: "default", payload: JSON.parse(postPayload) }),
  });
  setPostResult(await res.json());
}
```

Render: a section titled "Organic Channels (Phase 1)" with the dropdown, config textarea, payload textarea, buttons, and result JSON. When `postChannel` changes, set the payload template for that channel.

- [ ] **Step 2: Build to verify**

Run: `cd agency-frontend && npm run build`
Expected: SUCCESS (no compile errors)

- [ ] **Step 3: Commit**

```bash
cd agency-frontend
git add src/app/admin/social/page.js
git commit -m "feat(social): organic channels panel in Social Agent page"
```

---

### Task 16: full test pass + ship to EC2

**Files:**
- Modify: none (verification + deploy)
- Deploy script: reuse `deploy/deploy_website.py` pattern

**Interfaces:**
- Consumes: all tasks above

- [ ] **Step 1: Run the full backend test suite**

Run: `cd admin && python -m pytest tests/ -q`
Expected: no regressions — all previously passing tests still pass (existing suite ~76+ tests), plus new organic tests.

- [ ] **Step 2: Smoke-test the new endpoints locally**

Run:
```
cd admin && python main.py  # starts backend on :8000 (or configured port)
curl http://localhost:8000/api/social/organic/channels?workspace_id=default
curl -X POST http://localhost:8000/api/social/organic/post -H "Content-Type: application/json" -d "{\"channel\":\"reddit\",\"workspace_id\":\"default\",\"payload\":{}}"
```
Expected: channels list with 7 entries; post returns config_missing (no token) — both real responses.

- [ ] **Step 3: Deploy to EC2**

Follow the `deploy/deploy_website.py` one-shot pattern (bundle → scp → extract → py_compile → restart `sba.service` → verify `/api/health` + organic endpoints). Update `deploy/deploy_sba.py` if needed to include the new `admin/tools/organic/` package.

Run: `cd deploy && python deploy_sba.py`
Expected: DEPLOY OK, `/api/health` up, `/api/social/organic/channels` returns 7 channels.

- [ ] **Step 4: Commit deploy notes**

```bash
git add deploy/ docs/2026-08-05-social-organic-growth-engine-design.md
git commit -m "deploy(social): organic posting engine live on EC2"
```

---

## Self-Review Notes

- **Spec coverage:** Phase 1 spec sections covered — architecture (Tasks 1-4), per-platform API modules (Tasks 5-10), FB browser base (Task 11), social_tools integration (Task 12), API routes (Task 13), superpower skills (Task 14), frontend panel (Task 15), deploy (Task 16). Phase 2 (lead capture) and Phase 3 (autopilot/24-7) intentionally separate plans.
- **Placeholder scan:** FB browser module returns `queued` — documented as Phase 1b follow-up needing a live logged-in session; not a TBD, a deliberate contract decision with an explicit follow-up note.
- **Type consistency:** `PostResult` fields (`status`, `channel`, `post_id`, `post_url`, `error`, `published_at`) used consistently across hub, modules, and tests. `post(workspace_id, payload)` signature consistent in every module. Registry ids match CHANNEL_MODULES keys and token_manager platform keys.
