"""SBA Proactive Monitor — 24/7 background heartbeat for lead discovery.

Runs continuously and:
  1. Checks for stale leads needing follow-up
  2. Scans for new lead opportunities (via email)
  3. Monitors pipeline health and alerts CEO
  4. Auto-qualifies incoming leads
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Any

logger = logging.getLogger(__name__)

CHECK_INTERVAL_SECONDS = 10 * 60  # Every 10 minutes
LEAD_STALE_DAYS = 3  # Alert if lead untouched for 3+ days


class SBAMonitor:
    """Background monitor that keeps SBA pipeline running 24/7."""

    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._last_status: dict[str, Any] = {}
        self._status_lock = asyncio.Lock()
        self._ceo_alerts: list[dict[str, Any]] = []

    async def start(self) -> None:
        """Start the background monitoring loop."""
        logger.info("SBA Monitor started (interval=%ds)", CHECK_INTERVAL_SECONDS)
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
            logger.info("SBA Monitor stopped")

    async def get_pipeline_status(self) -> dict[str, Any]:
        """Get the latest pipeline status snapshot."""
        async with self._status_lock:
            if not self._last_status:
                self._last_status = await self._build_status()
            return self._last_status

    def get_ceo_alerts(self) -> list[dict[str, Any]]:
        """Get alerts that should be sent to CEO."""
        alerts = list(self._ceo_alerts)
        self._ceo_alerts.clear()
        return alerts

    async def _run_loop(self) -> None:
        """Main monitoring loop — runs forever."""
        while True:
            try:
                status = await self._build_status()
                async with self._status_lock:
                    self._last_status = status

                # Generate alerts for CEO
                for alert in status.get("alerts", []):
                    self._ceo_alerts.append(alert)
                    logger.info("SBA ALERT [%s]: %s", alert["severity"], alert["message"])

                # Auto-action: stale leads
                for stale in status.get("stale_leads", []):
                    logger.info("Stale lead detected: %s (last: %s)", stale["name"], stale["last_contact"])

                await asyncio.sleep(CHECK_INTERVAL_SECONDS)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("SBA Monitor error: %s", exc)
                await asyncio.sleep(60)

    async def _build_status(self) -> dict[str, Any]:
        """Build current SBA pipeline status snapshot."""
        from admin.agency.sba_store import list_handoffs, list_leads

        all_leads = list_leads()
        handoffs = [h for h in list_handoffs() if not h.get("workspace_id")]

        now = datetime.now(timezone.utc)
        alerts: list[dict[str, Any]] = []
        stale_leads: list[dict[str, Any]] = []
        hot_leads: list[dict[str, Any]] = []

        for lead in all_leads:
            updated = lead.get("updated_at", "")
            status = lead.get("status", "new")

            # Parse updated_at
            try:
                updated_dt = datetime.fromisoformat(updated) if updated else now
            except (ValueError, TypeError):
                updated_dt = now

            days_since_update = (now - updated_dt).days if updated_dt else 0

            # Flag stale leads
            if status in ("new", "contacted") and days_since_update >= LEAD_STALE_DAYS:
                stale_leads.append({
                    "id": lead["id"],
                    "name": lead.get("name", "Unknown"),
                    "business": lead.get("business_name", ""),
                    "status": status,
                    "last_contact": updated,
                    "days_stale": days_since_update,
                })
                if days_since_update >= 7:
                    alerts.append({
                        "severity": "warning",
                        "message": f"Lead '{lead.get('name', 'Unknown')}' stale for {days_since_update} days — needs follow-up",
                    })

            # Flag hot leads
            if lead.get("score", 0) >= 80 and status not in ("closed", "lost"):
                hot_leads.append({
                    "id": lead["id"],
                    "name": lead.get("name", "Unknown"),
                    "business": lead.get("business_name", ""),
                    "score": lead.get("score", 0),
                    "status": status,
                })

        # Pipeline summary
        pipeline_counts: dict[str, int] = {}
        for s in ["new", "contacted", "meeting", "proposal", "negotiation", "closed", "lost"]:
            pipeline_counts[s] = len([l for l in all_leads if l["status"] == s])

        if handoffs:
            alerts.append({
                "severity": "info",
                "message": f"{len(handoffs)} pending handoff(s) waiting for CEO action",
            })

        if hot_leads:
            alerts.append({
                "severity": "info",
                "message": f"{len(hot_leads)} hot lead(s) ready for CEO attention",
            })

        return {
            "timestamp": now.isoformat(),
            "pipeline": pipeline_counts,
            "total_leads": len(all_leads),
            "hot_leads": hot_leads,
            "stale_leads": stale_leads,
            "pending_handoffs": len(handoffs),
            "alerts": alerts,
        }


# Module-level singleton
_monitor: SBAMonitor | None = None


def get_monitor() -> SBAMonitor:
    global _monitor
    if _monitor is None:
        _monitor = SBAMonitor()
    return _monitor
