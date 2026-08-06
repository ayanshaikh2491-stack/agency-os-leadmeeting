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


def test_post_author_urn_not_doubled():
    # Full URN in person_urn must not be prefixed again (double-prefix hazard).
    with patch("admin.tools.organic.linkedin_api.get_active_token", return_value={"access_token": "li_token"}):
        with patch("admin.tools.organic.linkedin_api.requests.post") as mock_post:
            mock_post.return_value.ok = True
            mock_post.return_value.json.return_value = {"id": "post123"}
            result = post("ws1", {"text": "hi", "person_urn": "urn:li:person:abc"})
    body = mock_post.call_args.kwargs["json"]
    assert body["author"] == "urn:li:person:abc"

    # Partial urn form also normalizes to a single prefix.
    with patch("admin.tools.organic.linkedin_api.get_active_token", return_value={"access_token": "li_token"}):
        with patch("admin.tools.organic.linkedin_api.requests.post") as mock_post:
            mock_post.return_value.ok = True
            mock_post.return_value.json.return_value = {"id": "post124"}
            result = post("ws1", {"text": "hi", "person_urn": "person:abc"})
    body = mock_post.call_args.kwargs["json"]
    assert body["author"] == "urn:li:person:abc"
