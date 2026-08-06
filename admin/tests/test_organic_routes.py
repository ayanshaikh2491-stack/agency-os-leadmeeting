# admin/tests/test_organic_routes.py
from fastapi.testclient import TestClient

from admin.main import app

client = TestClient(app)


def test_organic_channels_route():
    resp = client.get("/api/social/organic/channels?workspace_id=default")
    assert resp.status_code == 200
    data = resp.json()
    assert "channels" in data
    assert any(c["id"] == "reddit" for c in data["channels"])


def test_organic_post_route_unknown_channel():
    resp = client.post("/api/social/organic/post", json={"channel": "nope", "workspace_id": "default", "payload": {}})
    assert resp.status_code == 200
    assert resp.json()["status"] == "error"


def test_organic_save_config_route():
    resp = client.post("/api/social/organic/config", json={"channel": "telegram", "workspace_id": "ws_test", "config": {"chat_id": "-100abc"}})
    assert resp.status_code == 200
    assert resp.json()["status"] == "saved"
