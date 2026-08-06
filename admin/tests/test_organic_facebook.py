from unittest.mock import patch

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
