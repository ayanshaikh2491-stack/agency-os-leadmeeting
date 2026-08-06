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
