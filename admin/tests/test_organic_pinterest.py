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
