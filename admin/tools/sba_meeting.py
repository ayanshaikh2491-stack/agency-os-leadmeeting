"""SBA Meeting Manager — Calendar + Meet links + store wrapper.

Handles the full meeting lifecycle:
  1. Create calendar event (Google Calendar via gws CLI)
  2. Generate meeting link (Google Meet)
  3. Store meeting record via existing sba_store
  4. Send confirmation emails via SBAEmailClient
"""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Any

from admin.agency import sba_store
from admin.tools.sba_email_client import SBAEmailClient, OWNER_NAME, OWNER_EMAIL
from admin.tools.sba_email_templates import format_template

logger = logging.getLogger(__name__)


class SBAMeetingManager:
    """Create and manage meetings with calendar integration."""

    def __init__(self) -> None:
        self._email = SBAEmailClient()

    async def create_meeting(
        self,
        lead_id: str,
        lead_name: str,
        lead_email: str,
        proposed_time: str,
        duration_minutes: int = 30,
    ) -> dict[str, Any]:
        """Full meeting setup: calendar event + link + email + store.

        Args:
            lead_id: Lead ID from sba_store.
            lead_name: Lead's display name.
            lead_email: Lead's email for invite.
            proposed_time: ISO format datetime string (e.g. '2026-07-30T14:00:00').
            duration_minutes: Meeting length.

        Returns: Meeting record dict.
        """
        # 1. Generate meeting link (Google Meet via calendar, or fallback)
        meeting_link = await self._generate_meet_link()

        # 2. Parse date/time from ISO string
        try:
            dt = datetime.fromisoformat(proposed_time)
            date_str = dt.strftime("%Y-%m-%d")
            time_str = dt.strftime("%H:%M")
        except Exception:
            date_str = proposed_time[:10]
            time_str = proposed_time[11:16] if len(proposed_time) >= 16 else "10:00"

        # 3. Try to create Google Calendar event
        calendar_event_id = await self._create_calendar_event(
            lead_name, lead_email, date_str, time_str, duration_minutes, meeting_link,
        )

        # 4. Store meeting record via existing sba_store API
        meeting = await sba_store.create_meeting({
            "lead_id": lead_id,
            "lead_name": lead_name,
            "title": f"Meeting: {lead_name} — TAGS Agency",
            "date": date_str,
            "time": time_str,
            "duration_minutes": duration_minutes,
            "status": "scheduled",
            "link": meeting_link,
            "notes": [f"Calendar event: {calendar_event_id or 'N/A'}"] if calendar_event_id else [],
            "transcript": "",
        })

        # 5. Send confirmation email to lead
        if lead_email:
            subject = f"✅ Confirmed! Meeting on {date_str}"
            body = format_template(
                "meeting_confirm",
                lead_name=lead_name,
                meeting_date=date_str,
                meeting_time=time_str,
                meeting_link=meeting_link,
                owner_name=OWNER_NAME,
            )
            await self._email.send_email(
                to_email=lead_email,
                subject=subject,
                body_text=body,
                cc_owner=True,
            )

        return meeting

    async def _generate_meet_link(self) -> str:
        """Generate a Google Meet link via gws CLI."""
        try:
            now = datetime.now(timezone.utc)
            start_str = now.strftime("%Y-%m-%dT%H:%M:%S")
            proc = await asyncio.create_subprocess_exec(
                "gws", "calendar", "insert",
                "--title", "SBA Meeting Placeholder",
                "--start", start_str,
                "--duration", "15",
                "--conference", "true",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate(timeout=15)
            output = stdout.decode("utf-8", errors="replace")
            match = re.search(r"(https?://meet\.google\.com/[-\w]+)", output)
            if match:
                return match.group(1)
        except Exception as exc:
            logger.warning("Google Meet link generation failed: %s", exc)

        # Fallback placeholder
        return f"https://meet.google.com/{datetime.now().strftime('%Y%m%d')}-sba-mtg"

    async def _create_calendar_event(
        self,
        lead_name: str,
        lead_email: str,
        date_str: str,
        time_str: str,
        duration_minutes: int,
        meeting_link: str,
    ) -> str | None:
        """Create Google Calendar event via gws CLI."""
        try:
            start_iso = f"{date_str}T{time_str}:00"
            proc = await asyncio.create_subprocess_exec(
                "gws", "calendar", "insert",
                "--title", f"Meeting: {lead_name} — TAGS Agency",
                "--description", f"SBA-scheduled meeting with {lead_name}.\nLink: {meeting_link}",
                "--start", start_iso,
                "--duration", str(duration_minutes),
                "--attendees", lead_email,
                "--attendees", OWNER_EMAIL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate(timeout=15)
            output = stdout.decode("utf-8", errors="replace").strip()
            return output or None
        except Exception as exc:
            logger.warning("Calendar event creation failed: %s", exc)
            return None

    async def update_meeting_status(
        self,
        meeting_id: str,
        status: str,
        notes: str = "",
    ) -> dict[str, Any] | None:
        """Update meeting status (completed, no_show, cancelled)."""
        updates: dict[str, Any] = {"status": status}
        if notes:
            if isinstance(notes, str):
                notes_list = [notes]
            else:
                notes_list = notes
            updates["notes"] = notes_list
        return await sba_store.update_meeting(meeting_id, updates)

    async def add_meeting_note(
        self,
        meeting_id: str,
        note: str,
    ) -> dict[str, Any] | None:
        """Add a note to an existing meeting."""
        return await sba_store.add_meeting_note(meeting_id, note)

    async def set_meeting_transcript(
        self,
        meeting_id: str,
        transcript: str,
    ) -> dict[str, Any] | None:
        """Attach a transcript to a meeting."""
        return await sba_store.set_meeting_transcript(meeting_id, transcript)

    async def set_meeting_summary(
        self,
        meeting_id: str,
        summary: str,
    ) -> dict[str, Any] | None:
        """Attach an AI-generated meeting summary."""
        meeting = sba_store.get_meeting(meeting_id)
        if not meeting:
            return None
        return await sba_store.update_meeting(meeting_id, {
            "summary": summary,
            "status": "done",
        })

    def get_meetings(
        self,
        lead_id: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        """List meetings, optionally filtered."""
        return sba_store.list_meetings(lead_id, status)

    def get_meeting(self, meeting_id: str) -> dict[str, Any] | None:
        """Get a single meeting record."""
        return sba_store.get_meeting(meeting_id)
