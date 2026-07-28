"""Test CEO proactive monitor."""
from __future__ import annotations

import sys
sys.path.insert(0, r"C:\Users\TAUSHEF\Downloads\int")

import pytest

pytestmark = pytest.mark.asyncio


async def test_monitor_import_and_create():
    from admin.agency.ceo_monitor import CEOMonitor

    monitor = CEOMonitor()
    assert monitor is not None


async def test_monitor_singleton():
    from admin.agency.ceo_monitor import get_monitor

    mon1 = get_monitor()
    mon2 = get_monitor()
    assert mon1 is mon2

