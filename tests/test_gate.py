from fastapi.testclient import TestClient
from admin.main import app


def test_direct_worker_chat_is_gated():
    client = TestClient(app)
    # content-creator IS in AGENT_SLUG_MAP, so it reaches the CEO gate (426)
    # rather than the 404 unknown-agent check.
    res = client.post("/api/agents/content-creator/chat", json={"message": "do outreach"})
    assert res.status_code in (400, 403, 426)
    body = res.json()
    assert "CEO" in body.get("detail", "") or "ceo" in str(body).lower()
