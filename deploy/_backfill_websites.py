"""One-shot backfill: scrape websites for existing leads, then enrich emails.

Runs on EC2 after the FIX10 deploy. Steps:
  1. Load all leads from Supabase.
  2. Group no-website leads by (category, city, state); scrape Google Maps
     cards (max 40) per target with the NEW card JS (which captures the
     website button link), match by name+phone, PATCH website.
  3. For leads that now have a website but no email, run domain-trust
     enrichment and PATCH the found email.

Usage: venv/bin/python _backfill_websites.py
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import sys
import time

sys.path.insert(0, ".")

from collections import Counter  # noqa: E402

# Single-instance guard: ssh retries can double-launch; only one backfill may run.
_PIDFILE = "/tmp/backfill_websites.pid"


def _claim_lock() -> bool:
    try:
        if os.path.exists(_PIDFILE):
            with open(_PIDFILE, encoding="utf-8") as f:
                old = int(f.read().strip() or "0")
            if old:
                os.kill(old, 0)  # alive?
                print("another backfill instance running (pid %s), exiting" % old, flush=True)
                return False
        with open(_PIDFILE, "w", encoding="utf-8") as f:
            f.write(str(os.getpid()))
        return True
    except Exception as exc:  # noqa: BLE001
        print("lock check failed (%s); continuing anyway" % exc, flush=True)
        return True


if not _claim_lock():
    sys.exit(0)

import admin.agency.sba_pipeline as pipe  # noqa: E402
from admin.tools.sba_lead_sources import find_leads  # noqa: E402
from admin.tools.lead_enrichment import find_lead_email  # noqa: E402


def now() -> str:
    return time.strftime("%H:%M:%S")


def log(*a) -> None:
    print(now(), *a, flush=True)


async def scrape_one(chrome, cat: str, city: str, state: str) -> list[dict]:
    """Scrape maps (with retries; Google throttles intermittently), then yelp
    as a website source fallback. Returns cards that carry a website."""
    cards: list[dict] = []
    for attempt in range(3):
        try:
            cards = await asyncio.wait_for(
                find_leads("google_maps", cat, city, state, max_candidates=40, chrome=chrome),
                timeout=200,
            )
            if any(c.get("website") for c in cards):
                return cards
        except Exception as exc:  # noqa: BLE001
            log("maps attempt", attempt + 1, "FAILED for", cat, city, state, "->", exc)
        await asyncio.sleep(25)
    # Yelp cards carry website links too; use them when maps is throttled.
    try:
        y = await asyncio.wait_for(
            find_leads("yelp", cat, city, state, max_candidates=40, chrome=chrome),
            timeout=90,
        )
        y = [c for c in y if c.get("website")]
        if y:
            log("yelp fallback for", cat, city, state, "->", len(y), "websites")
        cards = cards + y
    except Exception as exc:  # noqa: BLE001
        log("yelp fallback FAILED for", cat, city, state, "->", exc)
    return cards


def _norm_phone(p: str) -> str:
    """Digits-only, last 10; handles +1/E.164/dashes/parens."""
    d = re.sub(r"[^0-9]", "", p or "")
    if len(d) > 10 and d.startswith("1"):
        d = d[1:]
    return d


def patch_website(url, key, lead, site) -> bool:
    return pipe.sb_patch_lead(url, key, str(lead.get("id") or ""), {
        "website": site,
        "has_website": True,
        "website_status": "has_website",
    })


async def main() -> None:
    url, key = pipe.supabase_config()
    # Supabase occasionally times out on first read; retry until we have data.
    leads: list[dict] = []
    for attempt in range(6):
        leads = pipe.load_leads(url, key)
        if leads:
            break
        log("load_leads attempt", attempt + 1, "returned", len(leads), "; retrying in 15s")
        await asyncio.sleep(15)
    if not leads:
        log("FATAL: could not load leads from Supabase")
        return
    log("total leads:", len(leads))
    no_site = [l for l in leads if not (l.get("website") or "").strip()]
    with_email = [l for l in leads if (l.get("email") or "").strip()]
    log("no website:", len(no_site), "| with email:", len(with_email))

    # ── 1. Build (category, city, state) targets from no-website leads ──
    from collections import defaultdict
    by_key: dict[tuple, list[dict]] = defaultdict(list)
    counts: Counter = Counter()
    for l in no_site:
        cs = (l.get("city_state") or "").strip()
        parts = [p.strip() for p in cs.split(",") if p.strip()]
        city = parts[0] if parts else ""
        state = parts[1] if len(parts) > 1 else ""
        cat = (l.get("category") or "").strip()
        if cat and city:
            counts[(cat, city, state)] += 1
            by_key[(cat, city, state)].append(l)
    log("unique targets:", len(counts))
    # Cap at the highest-value targets (most missing-website leads). The
    # autopilot's own rotation backfills the rest over the coming passes.
    TOP_TARGETS = 30
    targets = counts.most_common(TOP_TARGETS)
    skipped_targets = len(counts) - len(targets)
    skipped_leads = sum(n for _, n in counts.most_common()[TOP_TARGETS:])
    log("processing top", len(targets), "targets (", len(counts), "total );",
        "skipping", skipped_targets, "targets covering", skipped_leads, "leads")

    from admin.tools import sba_lead_sources as src
    # Isolated Chrome: own CDP port + own profile dir so we never fight the
    # autopilot's managed daemon (shared daemon -> ERR_ABORTED navigations).
    chrome = src.ChromeTool(browser_name="sba-backfill", workspace="sba-backfill",
                            profile_dir=os.path.expanduser("~/.sba-backfill-profile"))

    refreshed = 0
    target_no = 0
    for (cat, city, state), n in targets:
        target_no += 1
        cards = await scrape_one(chrome, cat, city, state)
        if target_no <= 3:
            sample = [{"name": c.get("name"), "phone": c.get("phone"),
                       "website": c.get("website")} for c in cards[:5]]
            log("SAMPLE", cat, city, state, "->", json.dumps(sample))
        matched = 0
        for lead in by_key[(cat, city, state)]:
            if (lead.get("website") or "").strip():
                continue
            want_n = (lead.get("name") or "").strip().lower()
            want_p = _norm_phone(lead.get("phone") or "")
            if not want_n or not want_p:
                continue
            for card in cards:
                cn = (card.get("name") or "").strip().lower()
                cp = _norm_phone(card.get("phone") or "")
                site = (card.get("website") or "").strip()
                if cn == want_n and cp == want_p and site:
                    if patch_website(url, key, lead, site):
                        refreshed += 1
                        matched += 1
                        lead["website"] = site
                    break
        log(f"target {target_no}/{len(counts)} {cat} {city},{state} ({n} leads): "
            f"{len(cards)} cards ({sum(1 for c in cards if c.get('website'))} w/ website), "
            f"{matched} website matches, cumulative {refreshed}")

    # ── 2. Enrich emails for leads that have a website but no email ──
    sem = asyncio.Semaphore(4)

    def enrich_one(lead) -> None:
        name = (lead.get("name") or "").strip()
        if not name:
            return
        cs = (lead.get("city_state") or "").strip()
        city = cs.split(",")[0].strip() if cs else ""
        site = (lead.get("website") or "").strip()
        res = find_lead_email(name, city, lead.get("category") or "", site,
                              False, lead.get("id"))
        email = (res or {}).get("email") or ""
        prov = (res or {}).get("provenance") or ""
        if email:
            ok = pipe.sb_patch_lead(url, key, str(lead.get("id") or ""),
                                    {"email": email, "email_provenance": prov})
            log("EMAIL", name, "->", email, f"(provenance={prov}, patched={ok})")
        else:
            log("no email:", name, f"(domains={res.get('domains', [])[:1]})")

    async def run_one(lead) -> None:
        async with sem:
            try:
                await asyncio.wait_for(asyncio.to_thread(enrich_one, lead), timeout=150)
            except Exception as exc:  # noqa: BLE001
                log("enrich FAILED for", lead.get("name"), "->", exc)

    web_no_email = [l for l in leads if (l.get("website") or "").strip() and not (l.get("email") or "").strip()]
    log("website + no email (to enrich):", len(web_no_email))
    await asyncio.gather(*(run_one(l) for l in web_no_email))

    # ── 3. Final state ──
    leads2 = pipe.load_leads(url, key)
    log("FINAL total:", len(leads2))
    log("FINAL no website:", sum(1 for l in leads2 if not (l.get("website") or "").strip()))
    log("FINAL with email:", sum(1 for l in leads2 if (l.get("email") or "").strip()))
    log("DONE")


if __name__ == "__main__":
    asyncio.run(main())
