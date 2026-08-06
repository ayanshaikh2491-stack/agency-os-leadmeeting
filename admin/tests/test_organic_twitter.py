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
