# admin/tests/test_sba_time.py
import datetime as dt
import pytest

from admin.tools.sba_time import (
    STATE_TZ,
    human_time,
    lead_business_hours,
    lead_timezone,
    load_zone,
    meeting_slot,
    next_business_time,
    now_in,
)


def test_state_mapping():
    assert STATE_TZ["TX"] == "America/Chicago"
    assert STATE_TZ["CA"] == "America/Los_Angeles"
    assert STATE_TZ["NY"] == "America/New_York"


def test_now_in_returns_aware_datetime():
    now = now_in("America/Chicago")
    assert now.tzinfo is not None
    assert now.utcoffset() is not None


def test_lead_timezone_from_state():
    lead = {"state": "TX", "city": "Houston", "city_state": "Houston, TX"}
    assert lead_timezone(lead) == "America/Chicago"


def test_lead_timezone_from_city_state():
    lead = {"city_state": "Phoenix, AZ"}
    assert lead_timezone(lead) == "America/Phoenix"


def test_lead_business_hours_true_midday(monkeypatch):
    # Force a midday Texas time by patching now_in
    lead = {"state": "TX"}
    monkeypatch.setattr(
        "admin.tools.sba_time.now_in",
        lambda tz: dt.datetime(2026, 8, 3, 17, 0, tzinfo=dt.timezone.utc).astimezone(load_zone("America/Chicago")),
    )
    assert lead_business_hours(lead) is True


def test_lead_business_hours_false_night(monkeypatch):
    lead = {"state": "TX"}
    monkeypatch.setattr(
        "admin.tools.sba_time.now_in",
        lambda tz: dt.datetime(2026, 8, 3, 23, 0, tzinfo=dt.timezone.utc).astimezone(load_zone("America/Chicago")),
    )
    assert lead_business_hours(lead) is False


def test_next_business_time_is_future_9am():
    lead = {"state": "CA"}
    nxt = next_business_time(lead)
    parsed = dt.datetime.fromisoformat(nxt)
    assert parsed.tzinfo is not None
    assert parsed.hour == 9
    assert parsed > dt.datetime.now(dt.timezone.utc)


def test_meeting_slot_overlap():
    lead = {"state": "TX", "name": "Test Biz"}
    iso, text = meeting_slot(lead, owner_tz="Asia/Kolkata")
    parsed = dt.datetime.fromisoformat(iso)
    assert parsed.hour >= 9 and parsed.hour <= 17  # lead local business hours
    assert "India" in text and "US" in text


def test_human_time():
    out = human_time("2026-08-03T14:00:00", "Asia/Kolkata")
    assert isinstance(out, str) and out
