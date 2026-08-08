# STATE.md — Agency OS (SBA Lead-to-Meeting Pipeline)

> Purpose: one-page state so we never have to rescan the repo. Updated whenever
> the autopilot/agent status changes. Branch: `feat/sba-lead-to-meeting-pipeline`.

**Last updated:** 2026-08-08 17:56 IST (12:26 UTC)

---

## High Priority Tasks

1. **Autopilot healthy — 50+ passes, NRestarts=0** — DONE
   - Deployed `979ef71` (12:22 UTC): generic first-party email prefix fix (see #3).
   - Restart clean (12:22:48 UTC), fresh pass at 12:25 UTC complete normally.
2. **Website backfill COMPLETE** — DONE
   - Backfill finished 10:30 UTC: 670 leads, 487 no-website, 63 with email.
   - Only orphaned chrome (port 9252) remains; harmless.
3. **Enrichment yield fix DEPLOYED (`979ef71`, 12:22 UTC)** — ROOT CAUSE FOUND
   - **Bug:** `_JUNK_PREFIXES`/`_JUNK_EMAIL_PREFIXES` unconditionally blocked
     `info@`, `contact@`, `hello@`, `support@`, `admin@`, `office@`... But for a
     local small business those ARE the owner inbox. `allow_consumer` only
     relaxed the DOMAIN check, not the PREFIX check, so `info@beyondwow.com`
     (found on the business's own verified page) was rejected as junk.
   - **Fix:** split prefixes into `_GENERIC_*` (info/contact/hello/office/
     support/admin/sales/service/...) allowed ONLY when provenance proves the
     address came from the business's own verified page
     (consumer/own_domain/homepage), and `_HARD_JUNK_*` (noreply/unsubscribe/
     careers/press/billing/mailer/bounce/...) always rejected.
   - Applied in `admin/tools/lead_enrichment.py` (validity + crawl) AND
     `admin/agency/sba_autopilot.py` (send gate) AND `deploy/_backfill_websites.py`.
   - **Proof live:** `info@beyondwow.com` now enriches as `own_domain`
     (previously empty). Latest pass already shows `invalid_email: 5` (new
     allowed addresses being re-scored).
   - Re-enrichment batch running (124 website-having no-email leads, bypasses
     24h cooldown) to capture the fixed yield.
4. **LEADS ARE FLOWING** — multi-source, NOT just Google Maps
   - Autopilot `_find_new_leads` → `find_leads_all` loops **5 sources**:
     google_maps, yelp, yellowpages, bing_maps, facebook_pages.
   - DB 671 leads (latest). Enrichment state tracks 156 leads; ~60 tried in 2h.
5. **Email sends — still 0 today, 3 total historical**
   - 62 leads deferred to business hours (it is 6:26 AM CDT now; sends start
     ~14:00 UTC = 9 AM CDT, cap 30/day). Watch `emails_sent` after 14:00 UTC.
   - Once the re-enrichment lands, expect no_email 585 → lower.
6. **Memory pressure on EC2:** 1.9GiB total, swap active. Do NOT add heavier
   workloads to EC2.
7. **Email send cap / Gmail daily limit** — once sends start, watch for 550s;
   backoff is 24h per recipient and is already implemented.

---

## Agency Agents Status (EC2: 18.213.66.136, t3.small)

| Agent / Service | Status | Notes |
|---|---|---|
| `api/health` | ok | version 0.1.0, `ceo_ready: true`, workspace_count: 2 |
| `sba.service` | active | backend API |
| `sba-autopilot.service` | active | 24/7 loop, ~20 min cadence, NRestarts=0 after 979ef71 (12:22 UTC) |
| CEO agent | ready | orchestrator up |
| SBA (sales/business) | running | lead finding + enrichment + cold email + meetings |
| Ads / Content / SEO / Website / Analytics / Social | deployed | part of deploy bundle, not focus of current work |
| Email client (`SBAEmailClient`) | enabled: True | creds live on EC2 (.env), code falls back to `TAGS_SMTP_*` |
| Supabase (docker) | running | 671 leads, 604 no-email, 10 no-website |
| Organic engine (7 channels) | deployed | telegram/gbp/facebook browser + api channels |

Deploy: `python deploy/deploy_sba.py` (bundle → scp → extract → py_compile → restart → verify).
Verify after deploy: `autopilot/status` endpoint, `journalctl -u sba-autopilot.service`.

---

## Current Error Logs (recent, journalctl sba-autopilot)

```
Aug 08 08:53  ImportError build_workspace_email_client / TypeError email_client  <- crash-loop, FIXED 9e3e83e
Aug 08 10:30  backfill DONE: 670 leads, 487 no website, 63 with email (orphaned chrome only)
Aug 08 12:21  pass 50: emails_sent 0, no_email 587, deferred 62 (US pre-business-hours)
Aug 08 12:25  pass 51: invalid_email 5 (newly-allowed addresses being rescored), NRestarts=0
```

- No SMTP errors yet because no sends have happened (`send_failed: 0`).
- Leads ARE being judged each pass (Google Maps rotation active).
- `meetings` + `email_sends` tables do NOT exist in Supabase (PGRST205 when
  probed) — meetings are stored locally in `sba_store` SQLite in-memory; a
  Supabase meetings table may be a future hardening step.

---

## Current Issue Being Fixed (DO NOT RESCAN THE REPO)

**Problem (fixed `979ef71`, deployed 12:22 UTC):** 604 leads had no email, so
the pipeline stalled at step 2. Root cause found in the enrichment VALIDITY
GATE, not the crawl: generic first-party prefixes (info@/contact@/office@)
were unconditionally rejected even when the address came from the business's
own verified page. 124 leads HAVE websites; many expose exactly such addresses.

**Fix:** prefix lists split into generic (verified-only) vs hard-junk (always),
in both `lead_enrichment.py` and `sba_autopilot.py`. Provenance
consumer/own_domain/homepage now implies "verified first-party" and unlocks
generic prefixes; unverified scrapes still reject them.

**Proof:** `find_lead_email("Beyond Wow Plumbing & Drains", ..., site=beyondwow.com)`
now returns `info@beyondwow.com` (own_domain). Pass 51 already rescoring.

**Still open:** (a) re-enrichment batch running for the 124 website leads;
(b) ~480 leads with no website need Bing-based enrichment (slower, lower
yield); (c) 403/Cloudflare/JS-rendered sites (papermoonpainting, johnmooreservices,
texasqualityplumbing) need a headless browser for email extraction — NOT on
EC2 (memory); (d) sends start ~14:00 UTC — watch `emails_sent` and Gmail 550s.

---

## Recent Commits (this branch)

| Commit | What |
|---|---|
| `979ef71` | **generic first-party prefix fix (enrichment yield)** (current) |
| `1e5a733` | docs: STATE.md — crash-loop fixed, backfill running, leads flowing |
| `9e3e83e` | crash-loop fix + junk email gate + workspace email identity |
| `4c6dc28` | prioritize enrichment-ready leads + backfill phone-match fix |
| `0c1352c` | enrichment internal 38s budget + shrinking timeouts |
| `0711677` | enrichment state persistence + 45s wrapper timeout |
| `87ff421` | leads `website` column migration (PGRST204 fix) |
| `aa38243` | email client `TAGS_SMTP_*` env fallback |
| `f3efb99` | repo cleanup: removed scratch files, updated .gitignore |
| `0b03900` | capture `website` from Maps, os import, settle 8s |

## Run Log

- 09:05 UTC — backfill relaunched with junk gate (pid 2367341), 668 leads.
- 10:30 UTC — backfill DONE: 670 leads, 63 with email. Only orphaned chrome.
- 12:22 UTC — deployed `979ef71` (generic prefix fix), autopilot restarted
  clean, NRestarts=0.
- 12:25 UTC — pass 51: `invalid_email: 5`, `no_email: 585` (fix live).
- 12:26 UTC — re-enrichment batch started for 124 website-having no-email
  leads (bypasses 24h cooldown).

---

## SBA Workspace Isolation Audit (2026-08-08, code + live EC2)

**Question:** har client workspace ek alag (isolated) kaise hai?

**How isolation works (code, `admin/agency/sba_autopilot.py` + `sba_biztypes.py`):**
Each workspace gets its own `SBAAutopilot` instance (`run_all_once` loops
`list_sba_workspaces()`). Isolation key = `workspace_name` column on leads.

| Isolation domain | Mechanism | Verdict |
|---|---|---|
| Lead pool | `run_once` filters `workspace_name == self.workspace_name` before emailing; dedupe (name+phone) also workspace-scoped | ✅ isolated |
| New leads tagged | every saved row gets `workspace_name: self.workspace_name` | ✅ |
| Rotation cursor | per-workspace file `sba_rotation_{ws}.state` | ✅ |
| Outreach angle/strategy | per-workspace `sba_strategy_{ws}.json` | ✅ |
| Reasoning journal | per-workspace `sba_reasoning_{ws}.log` | ✅ |
| Owner email | `owner_email` from config; owner notifications + `_is_owner` use workspace owner (fallback agency OWNER_EMAIL) | ✅ |
| Reply handling | replies matched against THIS workspace's lead list only (email match); owner commands resolve only within workspace leads | ✅ |
| Meetings | created only from workspace-filtered leads; stored with `lead_id` (indirect scoping via lead) | ✅ (minor: meeting rows carry no `workspace_name` themselves) |

**Live status (EC2):**
- `sba_workspaces.json` does NOT exist on EC2 → `list_sba_workspaces()` runs
  **only the `agency` workspace** (it auto-injects agency when config missing).
- Supabase: **all leads are `workspace_name = agency`**. No client workspace
  is SBA-enabled yet.
- `api/health` `workspace_count: 2` counts the platform workspaces table (CEO
  workspaces), NOT SBA-enabled workspaces — don't confuse the two.

**Low-risk shared resources (note, not bugs):**
- **One shared Gmail inbox** for all workspaces (SMTP/IMAP creds are global).
  `check_replies(mark_read=True)` runs per workspace pass; with 2+ workspaces a
  reply could be consumed by whichever pass runs first. Today harmless (agency
  only), but a future per-workspace inbox or a `seen`-flag filter would harden it.
- **Enrichment cooldown file** `.sba_enrichment_state` is one shared file keyed
  by globally-unique lead id → no cross-contamination.
- **`client_id` on saved leads is hardcoded** to `00000000-...-0001` for all
  workspaces, but it is never read for filtering (isolation is by
  `workspace_name`) — dead metadata, low priority to fix.

**To enable a client workspace:** create `sba_workspaces.json` on EC2
(`{"<ws>": {"enabled": true, "owner_email": "...", "category": "..."}}`) or call
`set_workspace_config()`; next autopilot restart picks it up with its own
rotation/strategy/journal/owner and its own lead pool.
