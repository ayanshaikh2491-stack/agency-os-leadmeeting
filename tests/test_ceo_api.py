from fastapi.testclient import TestClient
from admin.main import app

def test_ceo_state_endpoint():
    client = TestClient(app)
    res = client.get("/api/ceo/state")
    assert res.status_code == 200
    body = res.json()
    # New lifecycle format: CEO is the 24/7 HTTP listener; agents are STANDBY
    # by default (no 24/7 loops). Every known agent should appear + be standby.
    assert body.get("ceo_listener") == "active_24x7_http"
    agents = {a["slug"]: a["state"] for a in body["agents"]}
    for slug in ("ceo", "sba", "seo", "social", "website"):
        assert slug in agents, f"missing agent {slug}"
        assert agents[slug] == "standby", f"{slug} should boot STANDBY"
    assert "rule" in body
