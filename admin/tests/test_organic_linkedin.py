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
