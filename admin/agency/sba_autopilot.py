# admin/agency/sba_autopilot.py
"""SBA 24/7 Autopilot — the always-on loop.

Never sleeps: repeatedly checks for work (new leads to email, replies to
process, meetings to confirm) and does it immediately. Emails are only sent
inside each lead's local business hours (human-style timing); everything
else (lead finding, drafting, planning) runs continuously.

Run:  python -m admin.agency.sba_autopilot
"""
from __future__ import annotations

import asyncio
import datetime as dt
import logging
import os
import random
import sys
from typing import Any

# Make sure project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from admin.agency import sba_pipeline as pipe  # noqa: E402
from admin.agency.sba_pipeline import (  # noqa: E402
    classify_reply,
    is_owner,
    load_leads,
    owner_notification_body,
    parse_owner_command,
    sb_patch_lead,
    supabase_config,
)
from admin.tools.sba_email_client import SBAEmailClient  # noqa: E402
from admin.tools.sba_email_draft import draft_email  # noqa: E402
from admin.tools.sba_meeting import SBAMeetingManager  # noqa: E402
from admin.tools.sba_time import (  # noqa: E402
    human_time,
    lead_business_hours,
    lead_timezone,
    meeting_slot,
    next_business_time,
    now_in,
)

logger = logging.getLogger("sba.autopilot")

INTERVAL_MINUTES = int(os.environ.get("SBA_AUTOPILOT_INTERVAL_MINUTES", "15"))
DAILY_EMAIL_CAP = int(os.environ.get("SBA_DAILY_EMAIL_CAP", "30"))
OWNER_TZ = os.environ.get("SBA_OWNER_TIMEZONE", "Asia/Kolkata")


class SBAAutopilot:
    """Always-on autonomous SBA loop."""

    def __init__(self, email_client: SBAEmailClient | None = None,
                 meeting_manager: SBAMeetingManager | None = None) -> None:
        self.email = email_client or SBAEmailClient()
        self.meetings = meeting_manager or SBAMeetingManager()
        self._last_status: dict[str, Any] = {"started": now_in(OWNER_TZ).isoformat()}

    def status(self) -> dict:
        return dict(self._last_status)

    async def _find_new_leads(self) -> int:
        """Run one lead-finding pass across platforms (best-effort)."""
        try:
            from admin.tools.sba_lead_sources import find_leads_all

            cfg = supabase_config()
            if not cfg:
                return 0
            url, key = cfg
            category = os.environ.get("SBA_LEAD_CATEGORY", "plumber")
            city = os.environ.get("SBA_LEAD_CITY", "Houston")
            state = os.environ.get("SBA_LEAD_STATE", "TX")
            leads = await find_leads_all(category, city, state, max_per_source=3)
            added = 0
            for lead in leads:
                lead["status"] = "new"
                lead["source_tag"] = ",".join(lead.get("sources") or [lead.get("source", "")])
                res = pipe.save_lead(url, key, lead)
                if res is not None:
                    added += 1
            logger.info("autopilot: found %d new leads from %d scraped", added, len(leads))
            return added
        except Exception as exc:  # noqa: BLE001
            logger.warning("lead finding pass failed: %s", exc)
            return 0

    async def _email_lead(self, url: str, key: str, lead: dict) -> str:
        """Send a professional cold email if lead is in business hours."""
        email = (lead.get("email") or "").strip()
        if not email:
            return "no_email"
        status = lead.get("status") or "new"
        if status in ("contacted", "meeting", "replied"):
            return "already_contacted"
        if not lead_business_hours(lead):
            return "deferred"
        subject, body = await draft_email(lead)
        ok = await self.email.send_email(to_email=email, subject=subject, body_text=body, cc_owner=True)
        if ok:
            sb_patch_lead(url, key, str(lead.get("id") or ""), {"status": "contacted", "email_status": "sent"})
            return "sent"
        return "send_failed"

    async def _process_replies(self, url: str, key: str, leads: list[dict]) -> dict[str, int]:
        stats = {"owner_notified": 0, "meetings_scheduled": 0, "rejected": 0}
        replies = await self.email.check_replies(mark_read=True)
        for rep in replies:
            from_addr = rep.get("from_addr", "")
            body = rep.get("body_preview", "") or rep.get("body_full", "")
            subject = rep.get("subject", "")
            if is_owner(from_addr):
                cmd = parse_owner_command(subject, body)
                lead = next((l for l in leads if str(l.get("id")) == str(cmd.get("lead_id"))), None)
                if not lead or cmd.get("action") == "unknown":
                    continue
                if cmd["action"] == "haan":
                    iso, text = meeting_slot(lead, OWNER_TZ)
                    await self.meetings.create_meeting(
                        lead_id=str(lead["id"]), lead_name=lead.get("name") or "Lead",
                        lead_email=lead.get("email") or "", proposed_time=iso,
                    )
                    sb_patch_lead(url, key, str(lead["id"]), {"status": "meeting"})
                    stats["meetings_scheduled"] += 1
                else:
                    await self.email.send_email(
                        to_email=lead.get("email") or "", subject="Thanks",
                        body_text=pipe.rejected_body(lead), cc_owner=True,
                    )
                    sb_patch_lead(url, key, str(lead["id"]), {"status": "rejected"})
                    stats["rejected"] += 1
            else:
                # Lead reply
                kind = classify_reply(body)
                lead = next((l for l in leads if (l.get("email") or "").lower() in from_addr.lower()), None)
                if not lead or kind != "yes":
                    continue
                await self.email.send_email(
                    to_email=from_addr, subject="Lead interested!",
                    body_text=owner_notification_body(lead, body[:300]), cc_owner=True,
                )
                sb_patch_lead(url, key, str(lead["id"]), {"status": "owner_confirm"})
                stats["owner_notified"] += 1
        return stats

    async def run_once(self) -> dict:
        """One full autopilot pass. Returns stats."""
        stats: dict[str, Any] = {
            "emails_sent": 0, "deferred_to_business_hours": 0, "no_email": 0,
            "send_failed": 0, "owner_notified": 0, "meetings_scheduled": 0,
            "rejected": 0, "new_leads_found": 0,
        }
        cfg = supabase_config()
        if not cfg:
            self._last_status.update(stats)
            return stats
        url, key = cfg
        leads = load_leads(url, key)
        sent = 0
        for lead in leads:
            if sent >= DAILY_EMAIL_CAP:
                break
            result = await self._email_lead(url, key, lead)
            if result == "sent":
                stats["emails_sent"] += 1
                sent += 1
            elif result == "deferred":
                stats["deferred_to_business_hours"] += 1
            elif result == "no_email":
                stats["no_email"] += 1
            elif result == "send_failed":
                stats["send_failed"] += 1
        reply_stats = await self._process_replies(url, key, leads)
        stats.update(reply_stats)
        stats["new_leads_found"] = await self._find_new_leads()
        stats["last_run"] = now_in(OWNER_TZ).isoformat()
        self._last_status = stats
        logger.info("autopilot pass: %s", stats)
        return stats

    async def run_forever(self) -> None:
        """Infinite loop — never sleeps, keeps checking for work."""
        logger.info("SBA autopilot starting (interval=%dm, cap=%d)", INTERVAL_MINUTES, DAILY_EMAIL_CAP)
        while True:
            try:
                await self.run_once()
            except Exception as exc:  # noqa: BLE001
                logger.exception("autopilot iteration failed: %s", exc)
            await asyncio.sleep(INTERVAL_MINUTES * 60)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    ap = SBAAutopilot()
    asyncio.run(ap.run_forever())


if __name__ == "__main__":
    main()
