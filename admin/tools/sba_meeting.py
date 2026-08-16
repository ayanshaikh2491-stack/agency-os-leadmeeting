"""SBA Meeting Manager — Google Calendar + Meet links + Meeting Records.

Handles the full meeting lifecycle:
  1. Generate Google Meet link
  2. Create Google Calendar event
  3. Store meeting record in sba_store
  4. Send confirmation email to lead

Relies on:
  - admin.agency.sba_store for CRUD
  - gws CLI for Google Calendar/Meet integration
  - SBAEmailClient for email notifications
  - sba_email_templates for email formatting
"""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from admin.agency import sba_store
from admin.tools.sba_email_client import SBAEmailClient, OWNER_NAME, OWNER_EMAIL
from admin.tools.sba_email_templates import format_template

logger = logging.getLogger(__name__)


class SBAMeetingManager:
    """Create and manage meetings with Google Calendar + Meet integration.

    Coordinates the meeting lifecycle:
      - Generates a Google Meet link
      - Creates a Calendar event with attendees
      - Persists the meeting record via sba_store
      - Sends a confirmation email to the lead
    """

    def __init__(self, email_client: SBAEmailClient | None = None) -> None:
        # Use the workspace's own inbox (client email identity), not a fresh
        # env-based client, so meeting confirmations come from the right owner.
        self._email = email_client or SBAEmailClient()

    async def create_meeting(
        self,
        lead_id: str,
        lead_name: str,
        lead_email: str,
        proposed_time: str,
        duration_minutes: int = 30,
        purpose: str = "",
    ) -> dict[str, Any]:
        """Full meeting setup: Meet link -> Calendar event -> Store -> Email.

        Args:
            lead_id: Lead ID from sba_store.
            lead_name: Lead's display name.
            lead_email: Lead's email for the calendar invite.
            proposed_time: ISO-format datetime string
                (e.g. ``"2026-08-01T15:00:00"``).
            duration_minutes: Meeting length in minutes.
            purpose: Meeting ka karan / agenda (optional).

        Returns:
            Meeting record dict as stored in sba_store.

        Raises:
            RuntimeError: if a real Google Meet link / Calendar event could not
            be booked (gws CLI unavailable or not authenticated). We deliberately
            do NOT fabricate a placeholder link and report success, because a
            silent fake "meet.google.com/..." URL would mislead the owner into
            thinking a real meeting was booked. Callers must handle this and
            fall back to a manual-booking record + owner notification.
        """
        # 1. Generate Google Meet link
        meeting_link = await self._generate_meet_link()
        if not meeting_link:
            # Real Meet link could not be created. Record a pending booking and
            # alert the owner instead of silently shipping a fake link.
            await self._record_pending_booking(
                lead_id=lead_id, lead_name=lead_name, lead_email=lead_email,
                proposed_time=proposed_time, duration_minutes=duration_minutes,
                purpose=purpose,
                reason="Google Meet link generation failed (gws CLI missing/unauthenticated)",
            )
            raise RuntimeError(
                "Meeting booking failed: no real Google Meet link. "
                "Owner notified for manual booking."
            )

        # 2. Create Google Calendar event with attendees
        calendar_event_id = await self._create_calendar_event(
            lead_name=lead_name,
            lead_email=lead_email,
            proposed_time=proposed_time,
            duration_minutes=duration_minutes,
            meeting_link=meeting_link,
        )
        if not calendar_event_id:
            await self._record_pending_booking(
                lead_id=lead_id, lead_name=lead_name, lead_email=lead_email,
                proposed_time=proposed_time, duration_minutes=duration_minutes,
                purpose=purpose,
                reason="Google Calendar event creation failed (gws CLI missing/unauthenticated)",
            )
            raise RuntimeError(
                "Meeting booking failed: calendar event not created. "
                "Owner notified for manual booking."
            )

        # 3. Build structured notes with calendar / meet metadata
        notes_list: list[dict[str, Any]] = []
        if calendar_event_id:
            notes_list.append({
                "type": "calendar_event",
                "id": calendar_event_id,
                "text": f"Calendar event created: {calendar_event_id}",
            })
        notes_list.append({
            "type": "meeting_link",
            "url": meeting_link,
            "text": f"Meeting link: {meeting_link}",
        })

        # Parse ISO time into date / time parts for sba_store
        dt = datetime.fromisoformat(proposed_time)

        # 4. Persist meeting record
        meeting = await sba_store.create_meeting({
            "lead_id": lead_id,
            "lead_name": lead_name,
            "title": f"Meeting with {lead_name} — TAGS Agency",
            "purpose": purpose,
            "date": dt.strftime("%Y-%m-%d"),
            "time": dt.strftime("%H:%M"),
            "duration_minutes": duration_minutes,
            "status": "scheduled",
            "notes": notes_list,
        })

        # 5. Send confirmation email to lead
        await self._email.send_email(
            to_email=lead_email,
            subject=f"Confirmed! Meeting on {proposed_time[:10]}",
            body_text=format_template(
                "meeting_confirm",
                lead_name=lead_name,
                meeting_date=proposed_time[:10],
                meeting_time=proposed_time[11:16],
                meeting_link=meeting_link,
                owner_name=OWNER_NAME,
            ),
            cc_owner=True,
        )

        return meeting

    # ── Internals ──────────────────────────────────────────────────────────

    async def _generate_meet_link(self) -> str:
        """Generate a Google Meet link via the gws CLI.

        Creates a brief placeholder calendar event with conference data
        (``--meet``) so Google returns a Meet URL. Falls back to a
        date-based placeholder only if the gws CLI is unavailable or
        returns no link.
        """
        try:
            now = datetime.now(timezone.utc)
            start = now.strftime("%Y-%m-%dT%H:%M:%S+00:00")
            end = (now + timedelta(minutes=15)).strftime("%Y-%m-%dT%H:%M:%S+00:00")
            proc = await asyncio.create_subprocess_exec(
                "gws", "calendar", "+insert",
                "--summary", "SBA Meeting Placeholder",
                "--start", start,
                "--end", end,
                "--attendee", OWNER_EMAIL,
                "--meet",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate(timeout=15)
            output = stdout.decode()
            match = re.search(r"(https?://meet\.google\.com/[-\w]+)", output)
            if match:
                return match.group(1)
        except Exception:
            logger.warning("Google Meet link generation failed, using placeholder")

        # No real link could be generated. Return empty so callers surface the
        # failure explicitly instead of sending a fake "confirmed" meeting.
        return ""

    async def _create_calendar_event(
        self,
        lead_name: str,
        lead_email: str,
        proposed_time: str,
        duration_minutes: int,
        meeting_link: str,
    ) -> str | None:
        """Create a Google Calendar event via the gws CLI with attendees."""
        try:
            start_dt = datetime.fromisoformat(proposed_time)
            end_dt = start_dt + timedelta(minutes=duration_minutes)
            proc = await asyncio.create_subprocess_exec(
                "gws", "calendar", "+insert",
                "--summary", f"Meeting: {lead_name} — TAGS Agency",
                "--description",
                f"SBA-scheduled meeting with {lead_name}.\nLink: {meeting_link}",
                "--start", start_dt.isoformat(),
                "--end", end_dt.isoformat(),
                "--attendee", lead_email,
                "--attendee", OWNER_EMAIL,
                "--meet",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate(timeout=15)
            event_id = stdout.decode().strip()
            if not event_id:
                # gws returned no event id (e.g. parse drift in output). Surface
                # the failure rather than recording a phantom calendar event.
                logger.warning("Calendar event created but no id returned by gws")
                return None
            return event_id
        except Exception as exc:
            logger.warning("Calendar event creation failed: %s", exc)
            return None

    # ── Manual-booking fallback (no silent fake link) ───────────────────────

    async def _record_pending_booking(
        self,
        lead_id: str,
        lead_name: str,
        lead_email: str,
        proposed_time: str,
        duration_minutes: int,
        purpose: str,
        reason: str,
    ) -> None:
        """Persist a pending manual-booking record and alert the owner.

        Used when the gws CLI cannot book a real meeting (binary missing or
        not authenticated). We never send the lead a fake confirmation; the
        owner is told to book manually.
        """
        try:
            dt = datetime.fromisoformat(proposed_time)
            await sba_store.create_meeting({
                "lead_id": lead_id,
                "lead_name": lead_name,
                "title": f"PENDING booking: {lead_name} — TAGS Agency",
                "purpose": purpose,
                "date": dt.strftime("%Y-%m-%d"),
                "time": dt.strftime("%H:%M"),
                "duration_minutes": duration_minutes,
                "status": "pending_manual_booking",
                "notes": [{
                    "type": "booking_failed",
                    "text": reason,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }],
            })
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not persist pending booking record: %s", exc)

        try:
            await self._email.send_email(
                to_email=OWNER_EMAIL,
                subject=f"Action needed: book meeting with {lead_name} manually",
                body_text=(
                    f"Hi {OWNER_NAME},\n\n"
                    f"The autopilot could not auto-book a Google Meet with "
                    f"{lead_name} ({lead_email}) for {proposed_time[:10]} "
                    f"{proposed_time[11:16]} ({duration_minutes} min).\n\n"
                    f"Reason: {reason}\n\n"
                    f"The lead has NOT been sent a confirmation. Please book this "
                    f"meeting manually and update the lead status.\n\n"
                    f"(This usually means the gws CLI is missing or not "
                    f"authenticated on the server.)"
                ),
                cc_owner=False,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Owner notification for pending booking failed: %s", exc)

    # ── Meeting CRUD helpers ───────────────────

    async def update_meeting_status(
        self,
        meeting_id: str,
        status: str,
        notes: str = "",
    ) -> dict[str, Any] | None:
        """Update meeting status (done, cancelled, etc.).

        Args:
            meeting_id: Meeting record ID.
            status: New status value.
            notes: Optional reason or note for the status change.

        Returns:
            Updated meeting dict, or None if the meeting was not found.
        """
        updates: dict[str, Any] = {"status": status}
        if notes:
            existing = sba_store.get_meeting(meeting_id)
            updated_notes = list(existing.get("notes", [])) if existing else []
            updated_notes.append({
                "type": "status_change",
                "status": status,
                "text": notes,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            updates["notes"] = updated_notes
        return await sba_store.update_meeting(meeting_id, updates)

    async def add_meeting_summary(
        self,
        meeting_id: str,
        summary: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Record an AI-generated meeting summary and mark as done.

        Args:
            meeting_id: Meeting record ID.
            summary: Dict with keys like ``text``, ``key_points``,
                ``action_items``, etc.

        Returns:
            Updated meeting dict, or None if not found.
        """
        return await sba_store.update_meeting(
            meeting_id,
            {
                "summary": summary.get("text", ""),
                "transcript_analysis": summary,
                "action_items": summary.get("action_items", []),
                "status": "done",
            },
        )

    async def add_meeting_note(
        self,
        meeting_id: str,
        text: str,
        speaker: str = "lead",
    ) -> dict[str, Any] | None:
        """Append a note to an existing meeting record.

        Args:
            meeting_id: Meeting record ID.
            text: Note content.
            speaker: Who said it (``"lead"``, ``"owner"``, ``"system"``).

        Returns:
            Updated meeting dict, or None if not found.
        """
        return await sba_store.add_meeting_note(
            meeting_id,
            text=text,
            speaker=speaker,
        )

    def get_meetings(
        self,
        lead_id: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        """List meetings, optionally filtered by lead or status.

        Args:
            lead_id: Filter by lead ID.
            status: Filter by status (``"scheduled"``, ``"done"``,
                ``"cancelled"``).

        Returns:
            Sorted list of meeting dicts (newest first).
        """
        return sba_store.list_meetings(lead_id, status)

    def get_meeting(self, meeting_id: str) -> dict[str, Any] | None:
        """Get a single meeting record by ID.

        Args:
            meeting_id: Meeting record ID.

        Returns:
            Meeting dict or None.
        """
        return sba_store.get_meeting(meeting_id)
