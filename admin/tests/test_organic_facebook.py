"""Tests for the Facebook browser module (Phase 1b ChromeTool flow).

Browser steps are exercised against a FakeChrome stand-in so no real Chrome
daemon or Facebook session is needed. post() itself keeps the hub contract:
config_missing without profile_dir, error on missing marketplace fields.
"""
import asyncio
from unittest.mock import patch

from admin.tools.organic.facebook_browser import (
    _is_marketplace,
    _post_to_group,
    _post_to_marketplace,
    post,
)


class FakeChrome:
    """Minimal ChromeTool stand-in recording browser actions."""

    def __init__(self):
        self.calls = []
        self.goto_result = {"text": "ok"}
        self.status_result = {"text": "✅ Connected | Facebook | https://www.facebook.com"}
        self.text_result = {"text": "Feed content with the posted message visible here"}
        self.click_ok = True
        self.fill_ok = True
        self.upload_ok = True
        # label -> {"selector": ..., "kind": "fill"|"click"} | None
        self.eval_map = {}

    async def status(self):
        return self.status_result

    async def close(self):
        self.calls.append(("close",))
        return {"text": "ok"}

    async def goto(self, url, **kw):
        self.calls.append(("goto", url))
        return self.goto_result

    async def wait(self, what, **kw):
        self.calls.append(("wait", what))
        return {"text": "ok"}

    async def eval_json(self, expr):
        self.calls.append(("eval_json", expr[:50]))
        for label, found in self.eval_map.items():
            if label in expr:
                return found
        return None

    async def click(self, selector=None, **kw):
        self.calls.append(("click", selector))
        return {"text": "ok"} if self.click_ok else {"error": "click boom"}

    async def fill(self, value, selector=None, **kw):
        self.calls.append(("fill", selector, value))
        return {"text": "ok"} if self.fill_ok else {"error": "fill boom"}

    async def upload(self, path, selector=None, **kw):
        self.calls.append(("upload", path, selector))
        return {"text": "ok"} if self.upload_ok else {"error": "upload boom"}

    async def screenshot(self):
        self.calls.append(("screenshot",))
        return {"text": "/tmp/sba_shot_x.png"}

    async def text(self):
        self.calls.append(("text",))
        return self.text_result


def _group_page_eval_map():
    return {
        "Write something": {"selector": '[aria-label="Write something..."]', "kind": "fill"},
        "Post": {"selector": '[aria-label="Post"]', "kind": "click"},
    }


def _marketplace_eval_map():
    return {
        "What are you selling?": {"selector": '[aria-label="What are you selling?"]', "kind": "fill"},
        "Price": {"selector": '[aria-label="Price"]', "kind": "fill"},
        "Description": {"selector": '[aria-label="Description"]', "kind": "fill"},
        "Publish": {"selector": '[aria-label="Publish"]', "kind": "click"},
    }


# ── Existing contract tests (unchanged) ────────────────────────────────────

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


def test_post_group_invalid_target():
    with patch("admin.tools.organic.facebook_browser.get_channel_config", return_value={"profile_dir": "x"}):
        result = post("ws1", {"target": "https://example.com", "message": "hi"})
    assert result.status == "error"
    assert "group URL" in result.error


def test_post_no_target_no_default_groups():
    with patch("admin.tools.organic.facebook_browser.get_channel_config", return_value={"profile_dir": "x"}):
        result = post("ws1", {"message": "hi"})
    assert result.status == "error"


# ── Group flow ─────────────────────────────────────────────────────────────

def test_group_flow_publishes():
    chrome = FakeChrome()
    chrome.eval_map = _group_page_eval_map()
    chrome.text_result = {"text": "Group feed showing: hello world posted just now"}
    result = asyncio.run(_post_to_group(chrome, "https://www.facebook.com/groups/123", {"message": "hello world"}, {}))
    assert result.status == "published"
    assert result.post_url == "https://www.facebook.com/groups/123"
    assert ("goto", "https://www.facebook.com/groups/123") in chrome.calls
    # message typed into the composer
    assert ("fill", '[aria-label="Write something..."]', "hello world") in chrome.calls
    assert ("click", '[aria-label="Post"]') in chrome.calls


def test_group_flow_missing_message_errors():
    chrome = FakeChrome()
    result = asyncio.run(_post_to_group(chrome, "https://www.facebook.com/groups/123", {}, {}))
    assert result.status == "error"
    assert "message" in result.error


def test_group_flow_composer_not_found():
    chrome = FakeChrome()
    chrome.eval_map = {}
    result = asyncio.run(_post_to_group(chrome, "https://www.facebook.com/groups/123", {"message": "hi"}, {}))
    assert result.status == "error"
    assert "composer" in result.error.lower()


def test_group_flow_post_button_missing_errors():
    chrome = FakeChrome()
    chrome.eval_map = _group_page_eval_map()
    chrome.eval_map.pop("Post")
    result = asyncio.run(_post_to_group(chrome, "https://www.facebook.com/groups/123", {"message": "hi"}, {}))
    assert result.status == "error"
    assert "Post button" in result.error


def test_group_flow_unverified_post_errors():
    chrome = FakeChrome()
    chrome.eval_map = _group_page_eval_map()
    chrome.text_result = {"text": "nothing relevant"}
    result = asyncio.run(_post_to_group(chrome, "https://www.facebook.com/groups/123", {"message": "not on page"}, {}))
    assert result.status == "error"
    assert "not verified" in result.error
    assert ("screenshot",) in chrome.calls


def test_group_flow_with_image_uploads():
    chrome = FakeChrome()
    chrome.eval_map = _group_page_eval_map()
    chrome.text_result = {"text": "feed showing: with pic posted just now"}
    with patch("admin.tools.organic.facebook_browser._download_image", return_value="/tmp/img.jpg"):
        result = asyncio.run(
            _post_to_group(chrome, "https://www.facebook.com/groups/123",
                           {"message": "with pic", "image_url": "https://x/y.jpg"}, {})
        )
    assert result.status == "published"
    assert ("upload", "/tmp/img.jpg", 'input[type="file"]') in chrome.calls


# ── Marketplace flow ───────────────────────────────────────────────────────

def test_marketplace_flow_publishes():
    chrome = FakeChrome()
    chrome.eval_map = _marketplace_eval_map()
    payload = {"title": "Office Chair", "price": "$120", "description": "Gently used", "image_url": "https://x/chair.jpg"}
    with patch("admin.tools.organic.facebook_browser._download_image", return_value="/tmp/chair.jpg"):
        result = asyncio.run(_post_to_marketplace(chrome, payload, {}))
    assert result.status == "published"
    assert ("goto", "https://www.facebook.com/marketplace/create/listing") in chrome.calls
    assert ("upload", "/tmp/chair.jpg", 'input[type="file"]') in chrome.calls
    assert ("fill", '[aria-label="What are you selling?"]', "Office Chair") in chrome.calls
    assert ("fill", '[aria-label="Price"]', "120") in chrome.calls
    assert ("fill", '[aria-label="Description"]', "Gently used") in chrome.calls
    assert ("click", '[aria-label="Publish"]') in chrome.calls


def test_marketplace_flow_no_photo_errors():
    chrome = FakeChrome()
    chrome.eval_map = _marketplace_eval_map()
    payload = {"title": "Chair", "price": "100"}
    with patch("admin.tools.organic.facebook_browser._download_image", return_value=None):
        result = asyncio.run(_post_to_marketplace(chrome, payload, {}))
    assert result.status == "error"
    assert "photo" in result.error


def test_marketplace_flow_missing_title_field_errors():
    chrome = FakeChrome()
    chrome.eval_map = _marketplace_eval_map()
    chrome.eval_map.pop("What are you selling?")
    payload = {"title": "Chair", "price": "100", "image_url": "https://x/y.jpg"}
    with patch("admin.tools.organic.facebook_browser._download_image", return_value="/tmp/y.jpg"):
        result = asyncio.run(_post_to_marketplace(chrome, payload, {}))
    assert result.status == "error"
    assert "title" in result.error


def test_marketplace_flow_publish_failure_errors():
    chrome = FakeChrome()
    chrome.eval_map = _marketplace_eval_map()
    chrome.eval_map.pop("Publish")
    payload = {"title": "Chair", "price": "100", "image_url": "https://x/y.jpg"}
    with patch("admin.tools.organic.facebook_browser._download_image", return_value="/tmp/y.jpg"):
        result = asyncio.run(_post_to_marketplace(chrome, payload, {}))
    assert result.status == "error"
    assert "publish failed" in result.error.lower()


# ── post() end-to-end with fake chrome ─────────────────────────────────────

def test_post_group_end_to_end():
    chrome = FakeChrome()
    chrome.eval_map = _group_page_eval_map()
    chrome.text_result = {"text": "Group feed showing: hello world posted just now"}
    with patch("admin.tools.organic.facebook_browser.get_channel_config", return_value={"profile_dir": "x"}):
        with patch("admin.tools.organic.facebook_browser._new_chrome", return_value=chrome):
            result = post("ws1", {"target": "https://www.facebook.com/groups/123", "message": "hello world"})
    assert result.status == "published"
    assert ("close",) in chrome.calls


def test_post_uses_default_group_from_config():
    chrome = FakeChrome()
    chrome.eval_map = _group_page_eval_map()
    chrome.text_result = {"text": "Group feed showing: to default group posted just now"}
    cfg = {"profile_dir": "x", "default_groups": ["https://www.facebook.com/groups/999"]}
    with patch("admin.tools.organic.facebook_browser.get_channel_config", return_value=cfg):
        with patch("admin.tools.organic.facebook_browser._new_chrome", return_value=chrome):
            result = post("ws1", {"message": "to default group"})
    assert result.status == "published"
    assert ("goto", "https://www.facebook.com/groups/999") in chrome.calls
