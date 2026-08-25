"""End-to-end proof: CEO HTTP endpoints drive Lifecycle state changes.

No 24/7 loops. CEO is the only 24/7 HTTP listener; agents self-sleep by default.
This test hits the REAL FastAPI routes (/api/ceo/state, /wake, /sleep) and
asserts the lifecycle actually flips.
"""
from fastapi.testclient import TestClient

from admin.main import app
from admin.agency import lifecycle as lc


def _client():
    # Fresh lifecycle table so the test is deterministic.
    lc._RUNTIMES.clear()  # noqa: SLF001
    return TestClient(app)


def test_ceo_state_all_standby_at_boot():
    c = _client()
    res = c.get("/api/ceo/state")
    assert res.status_code == 200
    body = res.json()
    assert body["ceo_listener"] == "active_24x7_http"
    states = {a["slug"]: a["state"] for a in body["agents"]}
    for slug in ("ceo", "sba", "seo", "social", "website"):
        assert states[slug] == "standby", f"{slug} must boot STANDBY"
    assert "rule" in body


def test_wake_then_sleep_flips_state_over_http():
    c = _client()
    # Boot snapshot -> sba standby
    assert c.get("/api/ceo/state").json()["agents"]
    sba_before = {a["slug"]: a["state"] for a in c.get("/api/ceo/state").json()["agents"]}["sba"]
    assert sba_before == "standby"

    # CEO/boss wakes sba over HTTP -> ACTIVE
    r = c.post("/api/ceo/agent/sba/wake")
    assert r.status_code == 200
    assert r.json()["state"] == "active"
    assert lc.get("sba").state.value == "active"

    # CEO/boss sleeps sba over HTTP -> STANDBY again
    r = c.post("/api/ceo/agent/sba/sleep")
    assert r.status_code == 200
    assert r.json()["state"] == "standby"
    assert lc.get("sba").state.value == "standby"


def test_no_route_conflict_resolves_to_new_state_shape():
    # The removed duplicate /state (old ceo_controller block) would NOT return
    # the lifecycle shape. Hitting /api/ceo/state and getting ceo_listener proves
    # the single, correct endpoint won (no conflict / no stale route).
    c = _client()
    res = c.get("/api/ceo/state")
    assert res.status_code == 200
    body = res.json()
    assert body.get("ceo_listener") == "active_24x7_http"
    # Old ceo_controller /state had none of these; proves new endpoint is live.
    assert "agents" in body and "rule" in body
