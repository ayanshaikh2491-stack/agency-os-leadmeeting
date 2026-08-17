"""Tests for the custom booking system living in the owner's store.

No real PocketBase is needed: we monkeypatch admin.store.store_store._api with
an in-memory fake that records requests and returns deterministic responses.
"""
import sys
import types

import pytest

from admin.store import store_store as ss


class _FakeApi:
    """In-memory replacement for store_store._api (Supabase/PocketBase gateway).

    Implements the real signature `_api(method, url, key, path, body=None,
    timeout=30, on_conflict="", profile="public")` and parses the PostgREST
    `path` (e.g. `/rest/v1/store_meetings?select=*&id=eq.X`) to route reads.
    """

    def __init__(self):
        self.records = {}  # table -> list[dict]
        self.calls = []

    def _table(self, table: str) -> list:
        return self.records.setdefault(table, [])

    @staticmethod
    def _parse_path(path: str):
        """Return (table, filters) from a PostgREST path.

        Handles `column=eq.value` operators. parse_qsl turns `id=eq.id_1` into
        key=id, value=eq.id_1, so we detect the operator from the value prefix.
        """
        import re
        import urllib.parse

        path_only = path.split("?", 1)[0]
        table = path_only.rstrip("/").split("/")[-1]
        filters = {}
        if "?" in path:
            qs = path.split("?", 1)[1]
            for key, val in urllib.parse.parse_qsl(qs):
                if key in ("select", "order", "limit", "on_conflict"):
                    continue
                m = re.match(r"^(eq|neq|gt|lt|gte|lte|like)\.(.*)$", val)
                if m:
                    filters[key] = m.group(2)
        return table, filters

    def __call__(self, method: str, url: str, key: str, path: str, body=None,
                 timeout: int = 30, on_conflict: str = "", profile: str = "public"):
        self.calls.append((method, path, body))
        table, filters = self._parse_path(path)
        rows = self._table(table)
        if method == "GET":
            out = rows
            for k, v in filters.items():
                out = [r for r in out if str(r.get(k, "")) == v]
            return out
        if method == "POST":
            # Emulate PostgREST upsert: on_conflict merges into the matching row.
            if on_conflict and on_conflict in (body or {}):
                ck = on_conflict
                cv = (body or {}).get(ck)
                for r in rows:
                    if r.get(ck) == cv:
                        r.update(body or {})
                        return [r]
            row = dict(body or {})
            if "id" not in row:
                row["id"] = "id_" + str(len(rows) + 1)
            rows.append(row)
            return [row]
        if method == "PATCH":
            rid = filters.get("id")
            for r in rows:
                if str(r.get("id")) == rid:
                    r.update(body or {})
                    return [r]
            return []
        if method == "DELETE":
            rid = filters.get("id")
            self.records[table] = [r for r in rows if str(r.get("id")) != rid]
            return []
        return []


@pytest.fixture
def fake_api(monkeypatch):
    api = _FakeApi()
    monkeypatch.setattr(ss, "_api", lambda *a, **k: api(*a, **k))
    monkeypatch.setattr(ss, "store_available", lambda: True)
    return api


def _seed_settings(api, client="Acme", **overrides):
    row = {
        "id": "s1",
        "client_name": client,
        "store_name": "Acme Store",
        "whatsapp": "+911234567890",
        "booking_enabled": False,
        "booking_slot_minutes": 30,
        "booking_working_hours": "09:00-18:00",
        "booking_timezone": "Asia/Kolkata",
        "booking_advance_hours": 1,
        "booking_slots": [],
    }
    row.update(overrides)
    api.records.setdefault(ss.SETTINGS_TABLE, []).append(row)
    return row


def test_booking_settings_normalized(fake_api):
    _seed_settings(fake_api)
    s = ss.get_booking_settings("agency", "Acme")
    # Defaults are normalized types, not raw strings.
    assert s["booking_enabled"] is False
    assert isinstance(s["booking_slot_minutes"], int) and s["booking_slot_minutes"] == 30
    assert s["booking_working_hours"] == "09:00-18:00"
    assert s["booking_timezone"] == "Asia/Kolkata"


def test_update_booking_settings_persists(fake_api):
    _seed_settings(fake_api)
    updated = ss.update_booking_settings("agency", "Acme", {
        "booking_enabled": True, "booking_slot_minutes": 45,
        "booking_working_hours": "10:00-17:00", "booking_timezone": "Asia/Kolkata",
    })
    assert updated["booking_enabled"] is True
    assert updated["booking_slot_minutes"] == 45
    again = ss.get_booking_settings("agency", "Acme")
    assert again["booking_enabled"] is True
    assert again["booking_slot_minutes"] == 45


def test_create_and_get_meeting(fake_api):
    _seed_settings(fake_api, booking_enabled=True)
    m = ss.create_meeting_request(
        "agency", "Acme",
        {
            "lead_id": "L1", "lead_name": "Al", "lead_email": "al@x.com",
            "lead_phone": "123", "date": "2026-09-01", "time": "10:00",
            "duration_minutes": 30, "notes": "intro call",
            "owner_link_base": "https://shop.example.com",
        },
    )
    assert m["id"]
    assert m["status"] == "requested"
    assert m["booking_token"]
    assert m["owner_link"] and "booking=" in m["owner_link"]

    fetched = ss.get_meeting_request("agency", "Acme", m["id"])
    assert fetched["id"] == m["id"]
    by_token = ss.find_meeting_by_token("agency", "Acme", m["booking_token"])
    assert by_token["id"] == m["id"]


def test_meeting_link_format(fake_api):
    _seed_settings(fake_api, booking_enabled=True)
    m = ss.create_meeting_request(
        "agency", "Acme",
        {"lead_id": "L4", "lead_name": "Di", "lead_email": "di@x.com",
         "owner_link_base": "https://shop.example.com"},
    )
    assert "/store/" in m["owner_link"]
    assert m["booking_token"] in m["owner_link"]


def test_meeting_status_transitions(fake_api):
    _seed_settings(fake_api, booking_enabled=True)
    m = ss.create_meeting_request(
        "agency", "Acme",
        {"lead_id": "L3", "lead_name": "Cy", "lead_email": "cy@x.com"},
    )
    confirmed = ss.update_meeting_request(
        "agency", "Acme", m["id"], {"status": "confirmed", "date": "2026-09-02", "time": "14:00"})
    assert confirmed["status"] == "confirmed"
    listed = ss.list_meeting_requests("agency", "Acme", status="confirmed")
    assert any(x["id"] == m["id"] for x in listed)


def test_sba_manager_raises_when_booking_disabled(fake_api):
    """SBAMeetingManager must refuse to book when the store disables booking."""
    _seed_settings(fake_api, booking_enabled=False)  # disabled
    from admin.tools.sba_meeting import SBAMeetingManager

    mgr = SBAMeetingManager(workspace="agency", client="Acme",
                            store_base_url="https://shop.example.com")

    async def go():
        with pytest.raises(RuntimeError):
            await mgr.create_meeting(
                lead_id="L2", lead_name="Bo", lead_email="bo@x.com",
                proposed_time="2026-09-01T10:00:00+05:30")

    import asyncio
    asyncio.run(go())


def test_sba_manager_books_when_enabled(fake_api):
    """When enabled, SBAMeetingManager persists a store_meetings row."""
    _seed_settings(fake_api, booking_enabled=True)
    from admin.tools.sba_meeting import SBAMeetingManager

    mgr = SBAMeetingManager(workspace="agency", client="Acme",
                            store_base_url="https://shop.example.com")

    async def go():
        meeting = await mgr.create_meeting(
            lead_id="L5", lead_name="Eve", lead_email="eve@x.com",
            proposed_time="2026-09-03T11:30:00+05:30")
        return meeting

    import asyncio
    meeting = asyncio.run(go())
    assert meeting["status"] == "requested"
    assert meeting["lead_name"] == "Eve"
    # A row was persisted in the fake store.
    assert any(r.get("lead_email") == "eve@x.com" for r in fake_api.records[ss.MEETINGS_TABLE])


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
