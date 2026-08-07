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
import re
import sys
import time
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
# Hard ceiling for one full pass. A wedged CDP/Supabase call (seen: 9h hang)
# must not freeze the loop; on timeout the pass is dropped and the browser
# handle is reset for the next iteration.
PASS_TIMEOUT_SECONDS = int(os.environ.get("SBA_AUTOPILOT_PASS_TIMEOUT_SECONDS", "1500"))
# Per-call ceiling for the lead-finding sub-pass (browser scraping).
LEAD_PASS_TIMEOUT_SECONDS = int(os.environ.get("SBA_LEAD_PASS_TIMEOUT_SECONDS", "900"))
# Max auto-enrichments (Bing + site crawls) per pass; each lead is retried at
# most once per 24h so we don't hammer search engines on every cycle.
MAX_ENRICH_PER_PASS = int(os.environ.get("SBA_MAX_ENRICH_PER_PASS", "8"))
OWNER_TZ = os.environ.get("SBA_OWNER_TIMEZONE", "Asia/Kolkata")
# Where the lead-rotation cursor lives so process restarts don't reset it.
# Without this, every deploy re-scrapes target #0 (all dupes -> 0 new leads).
_ROTATION_STATE_FILE = os.environ.get(
    "SBA_ROTATION_STATE_FILE",
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                 ".sba_rotation_state"),
)
# Don't re-hammer a recipient for 24h after an SMTP failure (Gmail 550
# daily-limit resets next day; retrying every 15 min just burns the limit).
EMAIL_RETRY_BACKOFF_SECONDS = int(os.environ.get("SBA_EMAIL_RETRY_SECONDS", str(24 * 3600)))

# ── Email sanity ─────────────────────────────────────────────────────────
# Only send cold emails to real-looking business addresses. The browser
# lead source scrapes contact hints that are often junk (support@discord,
# admissions@a-university, u003eaccountrecovery@deviantart, ...), so we
# gate sends behind a strict regex + a junk-domain blocklist.
_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
# TLDs that are never a real mailbox host (JS bundle filenames, placeholder
# domains, internal names). "preact@10.5.13.compat.module.min.js" passes the
# regex above, so we also reject file-extension TLDs and fake TLDs.
_JUNK_TLDS = {
    "js", "css", "png", "jpg", "jpeg", "gif", "svg", "webp", "html", "htm",
    "json", "xml", "php", "local", "internal", "invalid", "test", "example",
    "localhost", "donotuse", "company", "home", "lan", "intranet",
}
# Government/education/ISP-style domains are never a local business target.
_GOV_EDU_TLDS = ("gov", "edu", "mil")
_JUNK_EMAIL_DOMAINS = {
    "discord.com", "deviantart.com", "facebook.com", "instagram.com",
    "twitter.com", "x.com", "reddit.com", "youtube.com", "google.com",
    "gmail.com", "outlook.com", "yahoo.com", "hotmail.com", "aol.com",
    "zoho.com", "proton.me", "protonmail.com", "icloud.com", "me.com",
    "live.com", "msn.com", "qq.com", "163.com", "126.com", "tutanota.com",
    "github.com", "wikipedia.org", "quora.com", "linkedin.com", "tiktok.com",
    "pinterest.com", "snapchat.com", "whatsapp.com", "telegram.org",
    "starz.com", "visitdallas.com", "jetblue.com", "denison.edu", "hcfl.gov",
    "wellsfargo.com", "wellsfargoadvisors.com",
    # Media/news/consumer sites whose scraped "emails" are editorial addresses,
    # never a small-business decision maker.
    "wikihow.com", "zhihu.com", "biblegateway.com", "salon.com",
    "indianexpress.com", "grubhub.com", "rent.com", "joinbelle.com",
    "repeallouisville.com", "salemwebnetwork.com", "the-uptown.com",
    "52pojie.cn", "roamartists.com", "sa-comms.com", "whichiscorrect.com",
    "central.com", "volarerevere.com", "tnvacation.com", "midtownatl.com",
    "lenoxtools.com", "icstucson.org", "wiltondentalassoc.com",
    "districtgov.org", "bizjournals.com", "chamberofcommerce.com",
    "company.com", "yourdomain.com", "sentry.io", "wixpress.com",
    "godaddy.com", "domainsbyproxy.com", "googleusercontent.com",
}
# Consumer / free mailboxes (gmail, yahoo, ...). Many local small businesses
# run their business mailbox on these. They are only acceptable as a send
# target when email_provenance says the address came from the business's own
# verified page; without that flag they are junk (a random gmail is not a
# business decision maker).
_CONSUMER_DOMAINS = {
    "gmail.com", "googlemail.com", "yahoo.com", "yahoo.in", "yahoo.co.in",
    "hotmail.com", "hotmail.co.uk", "outlook.com", "live.com", "msn.com",
    "aol.com", "icloud.com", "me.com", "mac.com", "proton.me",
    "protonmail.com", "zoho.com", "qq.com", "163.com", "126.com",
    "tutanota.com", "gmx.com", "gmx.net", "mail.com", "yandex.com",
    "yandex.ru", "fastmail.com", "hey.com", "pm.me", "mail.ru",
    "rediffmail.com", "bol.com.br", "uol.com.br", "web.de", "orange.fr",
    "wanadoo.fr", "libero.it", "virgilio.it", "t-online.de", "btinternet.com",
    "sky.com", "virginmedia.com", "cox.net", "verizon.net", "att.net",
    "sbcglobal.net", "comcast.net", "charter.net", "earthlink.net",
    "frontiernet.net", "roadrunner.com", "optimum.net", "suddenlink.net",
}
# Domains that look like the *first party* but actually are just a big
# conglomerate/parent brand — not the local decision maker either.
_JUNK_EMAIL_PREFIXES = ("support@", "press@", "info@", "contact@", "admin@",
                        "noreply@", "no-reply@", "hello@", "help@", "sales@",
                        "billing@", "careers@", "jobs@", "hr@", "pr@",
                        "media@", "newsletter@", "unsubscribe@", "editor@",
                        "tips@", "newsroom@", "submissions@", "stories@",
                        "advertise@", "partners@", "founders@", "team@",
                        "privacy@", "legal@", "addressadmissions@",
                        "recreationdepartment@", "parkingservices@",
                        "mychartsupport@", "subscriptionsupport@",
                        "guest@", "stop@", "care@", "service@", "name@")
# Local parts that scream "automated/aggregator", not a human decision maker
# (ad-alerts@, notifications@, alert@, ...).
_JUNK_LOCAL_PAT = re.compile(
    r"(alert|notif|noreply|no-?reply|donotreply|automated|mailer|bounce|"
    r"postmaster|webmaster|abuse|marketing@|promo@|deals@|offers@)",
    re.I,
)
# A school/university/campus domain is not a small-business decision maker.
_SCHOOL_DOMAIN_MARKERS = (
    "school", "academy", "k12", "college", "univ", "campus", "faculty",
    "alumni", "edu.",
)
# HTML/JS-escape leftovers mean the scraped value is a mangled page fragment
# (e.g. "u003e" is the unicode escape for ">"), not a real mailbox.
_MALFORMED_TOKENS = ("u003e", "u003c", "%3e", "%3c", "&gt;", "&lt;", "\\u003e", "\\u003c")


# ── Lead discovery rotation ──────────────────────────────────────────────
# Each autopilot pass searches a different niche+city so new businesses keep
# arriving instead of re-scraping the same "plumber Houston" results forever.
# Override with SBA_LEAD_ROTATION=[["hvac","Dallas","TX"],...] (JSON).
_LEAD_TARGETS = [
    ("plumber", "Houston", "TX"),
    ("electrician", "San Antonio", "TX"),
    ("hvac", "Austin", "TX"),
    ("roofer", "Dallas", "TX"),
    ("landscaper", "Fort Worth", "TX"),
    ("auto repair", "Houston", "TX"),
    ("cleaning service", "San Antonio", "TX"),
    ("handyman", "Austin", "TX"),
    ("painter", "Dallas", "TX"),
    ("dentist", "Fort Worth", "TX"),
    ("plumber", "Austin", "TX"),
    ("electrician", "Houston", "TX"),
    ("hvac", "Dallas", "TX"),
    ("roofer", "San Antonio", "TX"),
    ("landscaper", "Houston", "TX"),
    ("auto repair", "Austin", "TX"),
    ("cleaning service", "Dallas", "TX"),
    ("handyman", "Fort Worth", "TX"),
    ("painter", "San Antonio", "TX"),
    ("salon", "Houston", "TX"),
    ("plumber", "Phoenix", "AZ"),
    ("electrician", "Atlanta", "GA"),
    ("hvac", "Charlotte", "NC"),
    ("roofer", "Tampa", "FL"),
    ("landscaper", "Orlando", "FL"),
    ("auto repair", "Denver", "CO"),
    ("cleaning service", "Las Vegas", "NV"),
    ("handyman", "Nashville", "TN"),
    ("painter", "Oklahoma City", "OK"),
    ("salon", "Memphis", "TN"),
    ("plumber", "San Diego", "CA"),
    ("electrician", "Columbus", "OH"),
    ("hvac", "Kansas City", "MO"),
    ("roofer", "New Orleans", "LA"),
    ("landscaper", "Louisville", "KY"),
    ("auto repair", "Albuquerque", "NM"),
    ("cleaning service", "Tulsa", "OK"),
    ("handyman", "El Paso", "TX"),
]



def _rotation_targets() -> list[tuple[str, str, str]]:
    raw = os.environ.get("SBA_LEAD_ROTATION", "")
    if raw:
        try:
            import json as _json

            items = _json.loads(raw)
            if items and all(isinstance(i, (list, tuple)) and len(i) == 3 for i in items):
                return [tuple(i) for i in items]
        except Exception:  # noqa: BLE001
            logger.warning("SBA_LEAD_ROTATION invalid, using default rotation")
    return list(_LEAD_TARGETS)


def _is_valid_lead_email(email: str, allow_consumer: bool = False) -> bool:
    """True only for a plausible business cold-email target.

    allow_consumer=True permits gmail/yahoo/... mailboxes, but ONLY when the
    caller can prove the address came from the business's own verified page
    (email_provenance == 'consumer' set by enrichment). Everything else is
    checked identically in both modes.
    """
    raw = (email or "").strip()
    if not raw:
        return False
    if any(tok in raw.lower() for tok in _MALFORMED_TOKENS):
        return False
    e = raw.lower()
    if not e or not _EMAIL_RE.match(e):
        return False
    if e == "test@example.com" or "example.com" in e:
        return False
    domain = e.split("@", 1)[1]
    local = e.split("@", 1)[0]
    tld = domain.rsplit(".", 1)[-1]
    if tld in _JUNK_TLDS:
        return False
    # gov/edu/mil — a municipality, school, or military site, not a local biz.
    if domain.endswith(_GOV_EDU_TLDS):
        return False
    # School/university/campus domains are never a local business mailbox.
    if any(m in domain for m in _SCHOOL_DOMAIN_MARKERS):
        return False
    if domain in _JUNK_EMAIL_DOMAINS:
        if allow_consumer and domain in _CONSUMER_DOMAINS:
            pass
        else:
            return False
    # Generic first-party catch-all prefixes are not a human decision maker.
    for prefix in _JUNK_EMAIL_PREFIXES:
        if e.startswith(prefix):
            return False
    if _JUNK_LOCAL_PAT.search(local):
        return False
    return True


class SBAAutopilot:
    """Always-on autonomous SBA loop."""

    def __init__(self, email_client: SBAEmailClient | None = None,
                 meeting_manager: SBAMeetingManager | None = None) -> None:
        self.email = email_client or SBAEmailClient()
        self.meetings = meeting_manager or SBAMeetingManager()
        self._last_status: dict[str, Any] = {"started": now_in(OWNER_TZ).isoformat()}
        self._target_idx = self._load_rotation_idx()
        self._email_retry_until: dict[str, float] = {}
        self._enriched_at: dict[str, float] = {}
        self._enrichments_this_pass = 0

    def _load_rotation_idx(self) -> int:
        try:
            with open(_ROTATION_STATE_FILE, encoding="utf-8") as f:
                return int(f.read().strip() or "0")
        except Exception:  # noqa: BLE001
            return 0

    def _save_rotation_idx(self, idx: int) -> None:
        try:
            with open(_ROTATION_STATE_FILE, "w", encoding="utf-8") as f:
                f.write(str(idx))
        except Exception:  # noqa: BLE001
            pass

    def status(self) -> dict:
        return dict(self._last_status)

    async def _find_new_leads(self) -> int:
        """Run one lead-finding pass across platforms (best-effort).

        Rotates through niche+city targets each pass, dedupes against leads
        already in Supabase, and saves rows in the leads table's column shape
        (raw JSONB carries the extra scraped fields).
        """
        try:
            from admin.tools.sba_lead_sources import find_leads_all

            cfg = supabase_config()
            if not cfg:
                return 0
            url, key = cfg
            targets = _rotation_targets()
            category, city, state = targets[self._target_idx % len(targets)]
            self._target_idx += 1
            self._save_rotation_idx(self._target_idx)
            logger.info(
                "lead rotation: %s in %s, %s (pass %d/%d)",
                category, city, state, self._target_idx, len(targets),
            )
            # Browser scraping can wedge on a dead CDP transport; bound it so
            # the autopilot loop always survives (previously hung 9h here).
            leads = await asyncio.wait_for(
                find_leads_all(category, city, state, max_per_source=5),
                timeout=LEAD_PASS_TIMEOUT_SECONDS,
            )

            # Dedupe against leads already stored (name + phone).
            existing = load_leads(url, key)
            existing_keys = set()
            for l in existing:
                n = (l.get("name") or "").strip().lower()
                p = (l.get("phone") or "").strip()
                if n and p:
                    existing_keys.add((n, p))

            added = 0
            for lead in leads:
                n = (lead.get("name") or "").strip().lower()
                p = (lead.get("phone") or "").strip()
                # Defensive: scrapers filter these, but never save a lead
                # without a phone or with a generic UI label as a name.
                if not n or not p:
                    continue
                if (n, p) in existing_keys:
                    continue
                row = {
                    "name": lead.get("name") or "",
                    "phone": lead.get("phone") or "",
                    "email": lead.get("email") or "",
                    "category": lead.get("category") or category,
                    "city_state": f"{city}, {state}",
                    "href": lead.get("href") or "",
                    "address": lead.get("address") or "",
                    "has_website": bool(lead.get("website")),
                    "website_status": "has_website" if lead.get("website") else "verified_none",
                    "mode": "card",
                    "text": lead.get("text") or "",
                    "raw": {
                        k: v for k, v in lead.items()
                        if k not in ("name", "phone", "email", "category", "city",
                                     "state", "href", "address", "website", "text")
                    },
                    "status": "candidate",
                    "workspace_name": "agency",
                    "client_id": "00000000-0000-0000-0000-000000000001",
                }
                res = pipe.save_lead(url, key, row)
                if res is not None:
                    added += 1
                    existing_keys.add((n, p))
            logger.info("autopilot: found %d new leads from %d scraped (%s in %s)",
                        added, len(leads), category, city)
            return added
        except Exception as exc:  # noqa: BLE001
            logger.warning("lead finding pass failed: %s", exc)
            return 0

    async def _enrich_lead_email(self, url: str, key: str, lead: dict) -> str:
        """Auto-fill a candidate lead's email via safe domain-trust enrichment.

        Only candidate leads get enriched (never re-contact already-contacted
        ones). The enrichment crawls only domains whose homepage mentions the
        business name, so grubhub.com/wikihow.com-type junk never gets saved.
        Returns (email, provenance); both '' when nothing trustworthy was found.
        """
        name = (lead.get("name") or "").strip()
        if not name:
            return "", ""
        city_state = lead.get("city_state") or lead.get("context", {}).get("city_state") or ""
        city = city_state.split(",")[0].strip() if city_state else ""
        try:
            from admin.tools.lead_enrichment import find_lead_email
        except Exception as exc:  # noqa: BLE001
            logger.warning("lead_enrichment import failed: %s", exc)
            return "", ""
        try:
            res = await asyncio.wait_for(
                asyncio.to_thread(
                    find_lead_email,
                    name,
                    city,
                    lead.get("category") or "",
                    lead.get("website") or "",
                    False,  # we PATCH below so failure is logged consistently
                    lead.get("id"),
                ),
                timeout=120,
            )
        except asyncio.TimeoutError:
            logger.info("enrichment timed out for %s", name)
            return "", ""
        except Exception as exc:  # noqa: BLE001
            logger.warning("enrichment failed for %s: %s", name, exc)
            return "", ""
        email = (res or {}).get("email") or ""
        provenance = (res or {}).get("provenance") or ""
        # Enrichment only collects consumer mailboxes from the business's own
        # verified page, so a consumer address it returns is trusted.
        if email and _is_valid_lead_email(email, allow_consumer=(provenance == "consumer")):
            logger.info("enriched %s -> %s (provenance=%s, sources=%s)",
                        name, email, provenance, res.get("domains"))
            self._email_retry_until.pop(email, None)
            return email, provenance
        return "", ""

    async def _email_lead(self, url: str, key: str, lead: dict) -> str:
        """Send a professional cold email if lead is in business hours."""
        email = (lead.get("email") or "").strip()
        provenance = (lead.get("email_provenance") or "").strip()
        status = lead.get("status") or "new"
        if status in ("contacted", "meeting", "replied", "owner_confirm"):
            return "already_contacted"
        if not email and status in ("candidate", "new") and self._enrichments_this_pass < MAX_ENRICH_PER_PASS:
            # Auto-enrichment: fill real business emails before giving up.
            # Each lead is tried at most once per 24h (Bing + site crawls are
            # expensive; a miss today is unlikely to be a hit tomorrow).
            lid = str(lead.get("id") or "")
            last_try = self._enriched_at.get(lid, 0.0)
            if time.time() - last_try > 24 * 3600:
                self._enriched_at[lid] = time.time()
                self._enrichments_this_pass += 1
                email, prov = await self._enrich_lead_email(url, key, lead)
                if email and not sb_patch_lead(url, key, lid, {"email": email, "email_provenance": prov}):
                    logger.warning("could not persist enriched email for %s", lead.get("name"))
                if email:
                    provenance = prov or provenance
        if not email:
            return "no_email"
        if not _is_valid_lead_email(email, allow_consumer=(provenance == "consumer")):
            logger.info("skip junk email %s for %s", email, lead.get("name") or "")
            return "invalid_email"
        # SMTP failure (e.g. Gmail 550 daily limit): don't re-hammer this
        # recipient until the backoff window has passed.
        blocked_until = self._email_retry_until.get(email)
        if blocked_until and time.time() < blocked_until:
            return "retry_backoff"
        if not lead_business_hours(lead):
            return "deferred"
        subject, body = await draft_email(lead)
        ok = await self.email.send_email(to_email=email, subject=subject, body_text=body, cc_owner=True)
        if ok:
            sb_patch_lead(url, key, str(lead.get("id") or ""), {"status": "contacted"})
            return "sent"
        self._email_retry_until[email] = time.time() + EMAIL_RETRY_BACKOFF_SECONDS
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
            "invalid_email": 0, "send_failed": 0, "owner_notified": 0,
            "meetings_scheduled": 0, "rejected": 0, "new_leads_found": 0,
            "retry_backoff": 0,
        }
        cfg = supabase_config()
        if not cfg:
            self._last_status.update(stats)
            return stats
        url, key = cfg
        self._enrichments_this_pass = 0
        leads = load_leads(url, key)
        attempts = 0
        for lead in leads:
            result = await self._email_lead(url, key, lead)
            if result == "sent":
                stats["emails_sent"] += 1
                attempts += 1
            elif result == "send_failed":
                stats["send_failed"] += 1
                attempts += 1
            elif result == "deferred":
                stats["deferred_to_business_hours"] += 1
            elif result == "no_email":
                stats["no_email"] += 1
            elif result == "invalid_email":
                stats["invalid_email"] += 1
            elif result == "retry_backoff":
                stats["retry_backoff"] += 1
            # Cap real SMTP attempts per pass (failed sends burned the whole
            # Gmail daily limit before this cap existed).
            if attempts >= DAILY_EMAIL_CAP:
                break
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
                # Bound every pass: a wedged CDP/Supabase call must never
                # freeze the loop (seen: autopilot hung 9h on a dead daemon
                # connection). Timeout -> log + stale playwright reset.
                await asyncio.wait_for(self.run_once(), timeout=PASS_TIMEOUT_SECONDS)
            except asyncio.TimeoutError:
                logger.exception("autopilot pass timed out after %ss — resetting browser handle", PASS_TIMEOUT_SECONDS)
                # Drop any stale playwright connection so the next pass
                # reconnects fresh instead of awaiting a dead transport.
                try:
                    await asyncio.wait_for(self._reset_chrome(), timeout=15)
                except Exception:  # noqa: BLE001
                    logger.warning("chrome handle reset failed (will retry next pass)")
            except Exception as exc:  # noqa: BLE001
                logger.exception("autopilot iteration failed: %s", exc)
            await asyncio.sleep(INTERVAL_MINUTES * 60)

    async def _reset_chrome(self) -> None:
        """Best-effort close of the cached ChromeTool connection."""
        try:
            from admin.agency import langgraph_sba as lg
            for ws in list(lg._chrome_registry.keys()):
                ch = lg._chrome_registry.pop(ws, None)
                if ch is not None:
                    try:
                        await asyncio.wait_for(ch.close(), timeout=10)
                    except Exception:  # noqa: BLE001
                        pass
        except Exception:  # noqa: BLE001
            pass


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    ap = SBAAutopilot()
    asyncio.run(ap.run_forever())


if __name__ == "__main__":
    main()
