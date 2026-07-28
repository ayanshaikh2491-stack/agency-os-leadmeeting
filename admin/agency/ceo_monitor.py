"""CEO Proactive Monitor — background heartbeat watching the agency.

Runs every 15 minutes and checks:
  1. Token health → alerts if expiring/expired
  2. Pending reviews → count of reviews needing CEO attention
  3. SBA handoffs → pending handoffs waiting for CEO
  4. Workspace activity → inactive workspaces (7+ days no activity)
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

CHECK_INTERVAL_SECONDS = 15 * 60  # Every 15 minutes


class CEOMonitor:
    """Background monitor that keeps CEO informed of agency health."""

    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._last_status: dict[str, Any] = {}
        self._status_lock = asyncio.Lock()

    async def start(self) -> None:
        """Start the background monitoring loop."""
        logger.info("CEO Monitor started (interval=%ds)", CHECK_INTERVAL_SECONDS)
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        """Stop the background monitoring loop."""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
            logger.info("CEO Monitor stopped")

    async def get_agency_status(self) -> dict[str, Any]:
        """Get the latest agency status snapshot."""
        async with self._status_lock:
            if not self._last_status:
                self._last_status = await self._build_status()
            return self._last_status

    async def _run_loop(self) -> None:
        """Main monitoring loop."""
        while True:
            try:
                status = await self._build_status()
                async with self._status_lock:
                    self._last_status = status

                for alert in status.get("alerts", []):
                    logger.warning("CEO ALERT [%s]: %s", alert["severity"], alert["message"])

                await asyncio.sleep(CHECK_INTERVAL_SECONDS)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("CEO Monitor error: %s", exc)
                await asyncio.sleep(60)

    async def _build_status(self) -> dict[str, Any]:
        """Build current agency status snapshot."""
        from admin.ceo_data import get_agency_overview
        overview = get_agency_overview()

        from admin.workspace.manager import list_pending_reviews
        pending_reviews = list_pending_reviews()

        try:
            from admin.agency.sba_store import list_handoffs
            handoffs = [h for h in list_handoffs() if not h.get("workspace_id")]
        except ImportError:
            handoffs = []

        alerts = list(overview.get("alerts", []))

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "workspace_count": overview["summary"].get("total_workspaces", 0),
            "pending_reviews": len(pending_reviews),
            "pending_handoffs": len(handoffs),
            "alerts": alerts,
            "token_health": {
                "total": overview["summary"].get("total_tokens", 0),
                "expired": overview["summary"].get("expired_tokens", 0),
                "expiring": overview["summary"].get("expiring_tokens", 0),
            },
            "leads": {
                "active": overview["summary"].get("active_leads", 0),
                "closed": overview["summary"].get("closed_leads", 0),
            },
        }


# Module-level singleton
_monitor: CEOMonitor | None = None


def get_monitor() -> CEOMonitor:
    global _monitor
    if _monitor is None:
        _monitor = CEOMonitor()
    return _monitor

