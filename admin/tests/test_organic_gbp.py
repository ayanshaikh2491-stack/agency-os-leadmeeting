from unittest.mock import patch

from admin.tools.organic.gbp_api import post


def test_post_no_token():
    with patch("admin.tools.organic.gbp_api.get_active_token", return_value=None):
        result = post("ws1", {"summary": "s"})
    assert result.status == "config_missing"


def test_post_ok():
    with patch("admin.tools.organic.gbp_api.get_active_token", return_value={"access_token": "gbp_tok"}):
        with patch("admin.tools.organic.gbp_api.get_channel_config", return_value={"location_name": "accounts/1/locations/2"}):
            with patch("admin.tools.organic.gbp_api.requests.post") as mock_post:
                mock_post.return_value.ok = True
                mock_post.return_value.json.return_value = {"name": "accounts/1/locations/2/localPosts/3"}
                result = post("ws1", {"summary": "hello gbp"})
    assert result.status == "published"
    assert result.post_id == "accounts/1/locations/2/localPosts/3"
