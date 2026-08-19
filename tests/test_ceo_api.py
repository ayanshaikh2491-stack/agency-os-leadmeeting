from fastapi.testclient import TestClient
from admin.main import app

def test_ceo_state_endpoint():
    client = TestClient(app)
    res = client.get("/api/ceo/state")
    assert res.status_code == 200
    body = res.json()
    assert "workers" in body and "mandates" in body and "floor" in body
