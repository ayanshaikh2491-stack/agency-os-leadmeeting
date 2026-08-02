# admin/tests/test_autopilot_integration.py
from admin.config import settings
from admin.tools.chrome_tool import CHROME_TOOLS


def test_chrome_tools_include_lead_source_tools():
    names = [t["function"]["name"] for t in CHROME_TOOLS]
    assert "sba_find_leads" in names
    assert "sba_find_leads_all" in names


def test_settings_have_autopilot_defaults():
    assert hasattr(settings, "sba_owner_timezone")
    assert settings.sba_owner_timezone == "Asia/Kolkata"
    assert settings.sba_autopilot_interval_minutes == 15
    assert settings.sba_daily_email_cap == 30
