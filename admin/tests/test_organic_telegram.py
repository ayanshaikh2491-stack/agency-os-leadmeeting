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
