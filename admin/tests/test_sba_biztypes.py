# admin/tests/test_sba_biztypes.py
"""Tests for the per-workspace SBA business-type classifier (no network)."""
import json

import pytest

from admin.agency import sba_biztypes as bt


@pytest.fixture(autouse=True)
def _isolated_config(monkeypatch, tmp_path):
    """Point the workspaces config file at a temp dir per test."""
    f = tmp_path / "sba_workspaces.json"
    monkeypatch.setattr(bt, "CONFIG_FILE", str(f))
    return f


def _write_config(path, data):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


# ── classify_business ────────────────────────────────────────────────────────


def test_classify_d2c_needs_sba_false():
    res = bt.classify_business("shopify-store", industry="D2C ecommerce brand")
    assert res["needs_sba"] is False


def test_classify_ecommerce_description_false():
    res = bt.classify_business("acme", description="online retail store selling apparel")
    assert res["needs_sba"] is False


def test_classify_software_false():
    res = bt.classify_business("myco", industry="SaaS software")
    assert res["needs_sba"] is False


def test_classify_real_estate_true():
    res = bt.classify_business("bob", industry="real estate")
    assert res["needs_sba"] is True
    assert res["category"] == "real estate"
    assert res["rotation"]
    assert res["angle"]


def test_classify_plumbing_true():
    res = bt.classify_business("bob", description="we are a plumbing contractor")
    assert res["needs_sba"] is True
    assert res["category"] == "plumbing"


def test_classify_unknown_false():
    res = bt.classify_business("mystery-co", industry="quantum consulting")
    assert res["needs_sba"] is False
    assert res["category"] == ""
    assert res["rotation"] == []


def test_classify_agency_always_true():
    for name in ("agency", "AGENCY", "Agency"):
        res = bt.classify_business(name)
        assert res["needs_sba"] is True
        assert res["category"] == "local business"
        assert res["angle"]
        assert len(res["rotation"]) == len(bt.DEFAULT_ROTATION)


# ── get / set workspace config ───────────────────────────────────────────────


def test_get_workspace_config_defaults_without_file():
    cfg = bt.get_workspace_config("agency")
    assert cfg["name"] == "agency"
    assert cfg["needs_sba"] is True
    assert cfg["enabled"] is True
    assert cfg["owner_email"] == ""
    assert cfg["category"] == "local business"


def test_set_get_roundtrip(tmp_path, monkeypatch):
    f = tmp_path / "sba_workspaces.json"
    monkeypatch.setattr(bt, "CONFIG_FILE", str(f))
    assert bt.set_workspace_config(
        "bob",
        enabled=True,
        owner_email="bob@example.com",
        industry="real estate",
        category="real estate",
        rotation=[["realtor", "Dallas", "TX"]],
        angle="Help local realtors win more listings",
    )
    cfg = bt.get_workspace_config("bob")
    assert cfg["enabled"] is True
    assert cfg["needs_sba"] is True
    assert cfg["owner_email"] == "bob@example.com"
    assert cfg["industry"] == "real estate"
    assert cfg["category"] == "real estate"
    assert cfg["rotation"] == [["realtor", "Dallas", "TX"]]
    assert cfg["angle"] == "Help local realtors win more listings"


def test_persisted_override_beats_classification(tmp_path, monkeypatch):
    f = tmp_path / "sba_workspaces.json"
    monkeypatch.setattr(bt, "CONFIG_FILE", str(f))
    # Classified as needing SBA, but owner disables it.
    assert bt.set_workspace_config("bob", enabled=False, industry="plumbing")
    cfg = bt.get_workspace_config("bob")
    assert cfg["needs_sba"] is False
    assert cfg["enabled"] is False
    # Industry override survives.
    assert cfg["industry"] == "plumbing"


def test_set_workspace_config_ignores_unknown_keys(tmp_path, monkeypatch):
    f = tmp_path / "sba_workspaces.json"
    monkeypatch.setattr(bt, "CONFIG_FILE", str(f))
    assert bt.set_workspace_config("bob", bogus_key="nope", owner_email="x@y.z") is True
    cfg = bt.get_workspace_config("bob")
    assert cfg["owner_email"] == "x@y.z"
    with open(f, encoding="utf-8") as fh:
        stored = json.load(fh)
    assert "bogus_key" not in stored["bob"]


# ── list_sba_workspaces ──────────────────────────────────────────────────────


def test_list_includes_agency_by_default():
    ws = bt.list_sba_workspaces()
    names = {w["name"] for w in ws}
    assert "agency" in names
    agency = next(w for w in ws if w["name"] == "agency")
    assert agency["category"] == "local business"
    assert agency["owner_email"] == ""
    assert agency["rotation"]
    assert agency["angle"]


def test_list_only_enabled(tmp_path, monkeypatch):
    f = tmp_path / "sba_workspaces.json"
    monkeypatch.setattr(bt, "CONFIG_FILE", str(f))
    bt.set_workspace_config("bob", enabled=True, owner_email="b@example.com")
    bt.set_workspace_config("sue", enabled=False)
    names = {w["name"] for w in bt.list_sba_workspaces()}
    assert "bob" in names
    assert "sue" not in names


def test_list_never_raises_on_corrupt_file(tmp_path, monkeypatch):
    f = tmp_path / "sba_workspaces.json"
    monkeypatch.setattr(bt, "CONFIG_FILE", str(f))
    f.write_text("{not valid json", encoding="utf-8")
    # Corrupt config degrades to empty, so the agency default still appears;
    # the contract is that it never raises.
    ws = bt.list_sba_workspaces()
    assert isinstance(ws, list)
    assert "agency" in {w["name"] for w in ws}


# ── paths ────────────────────────────────────────────────────────────────────


def test_strategy_path_sanitizes():
    assert bt.strategy_path("Agency Biz!") == "/home/ubuntu/sba-backend/sba_strategy_agency_biz_.json"
    assert bt.strategy_path("bob") == "/home/ubuntu/sba-backend/sba_strategy_bob.json"


def test_journal_path_sanitizes():
    assert bt.journal_path("Web Works") == "/home/ubuntu/sba-backend/sba_reasoning_web_works.log"
    assert bt.journal_path("Bob's-Plumbing") == "/home/ubuntu/sba-backend/sba_reasoning_bob_s_plumbing.log"


def test_rotation_state_path_sanitizes():
    assert bt.rotation_state_path("Agency") == "/home/ubuntu/sba-backend/sba_rotation_agency.state"
