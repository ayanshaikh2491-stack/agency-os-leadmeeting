# admin/tests/test_organic_base.py
import sys
sys.path.insert(0, r"C:\Users\TAUSHEF\Downloads\int")

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
