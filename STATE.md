# STATE.md — Agency OS (SBA Lead-to-Meeting Pipeline)

> Purpose: one-page state so we never have to rescan the repo. Updated whenever
> the autopilot/agent status changes. Branch: `feat/sba-lead-to-meeting-pipeline`.

**Last updated:** 2026-08-08 15:10 IST (09:40 UTC)

---

## High Priority Tasks

1. **Autopilot crash-loop FIXED (`9e3e83e`, deployed 08:53-08:57 UTC)** — DONE
   - Root cause: EC2 had STALE copies of `sba_email_client.py` (missing
     `build_workspace_email_client`), `sba_meeting.py` (missing `email_client`
     kwarg), `sba_biztypes.py` + `sba.py` (workspace email identity changes).
     systemd restarted 19x with ImportError / TypeError.
   - Fixed: scp'd all 4 files, import check OK, restarted. `NRestarts=0`, pid
     alive, fresh pass at 09:02 + 09:39 UTC both complete normally.
2. **Junk email gate DEPLOYED** — fake/aggregator emails now rejected
   - `_JUNK_EMAIL_PREFIXES`: feedback@, hi@. `_JUNK_EMAIL_DOMAINS`: ground.news,
     mystore.com, wixsite.com, myshopify.com, squarespace.com, godaddysites.com,
     weebly.com, wordpress.com. Backfill gate uses `_is_valid_lead_email`
     (`allow_consumer` only when provenance == consumer). Junk rows cleaned.
3. **Website backfill RUNNING (relaunched 09:05 UTC, pid 2367341)**
   - 668 leads loaded, 521 no-website, 60 unique (cat,city,state) targets, top
     30 processed. Website capture works (SAMPLE shows real domains). Google
     throttling causes transient CDP errors → retry + yelp fallback built in.
   - Email enrichment phase runs after scrape (~31 website+no-email leads).
4. **LEADS ARE FLOWING** — Google Maps sourcing active
   - DB 668 → 670 leads. 09:39 pass judged 4 auto-repair Houston leads
     (J&T Automotive 85, King of rim repair 85, Firestone 0, Helfman Ford 10).
     Newest lead rows timestamp 09:39 UTC. `new_leads_found=0` in pass_summary
     is misleading (judged existing + newly-scraped leads, count is 0 metric bug).
5. **Email count 31** (28 clean + backfill). Emails still not SENT — sends are
   gated behind email enrichment + business-hours; keep watching `emails_sent`.
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
| `sba-autopilot.service` | active | 24/7 loop, ~20 min cadence, NRestarts=0 after crash-loop fix (09:53 UTC) |
| CEO agent | ready | orchestrator up |
| SBA (sales/business) | running | lead finding + enrichment + cold email + meetings |
| Ads / Content / SEO / Website / Analytics / Social | deployed | part of deploy bundle, not focus of current work |
| Email client (`SBAEmailClient`) | enabled: True | creds live on EC2 (.env), code falls back to `TAGS_SMTP_*` |
| Supabase (docker) | running | `leads.website` column added via migration |
| Organic engine (7 channels) | deployed | telegram/gbp/facebook browser + api channels |

Deploy: `python deploy/deploy_sba.py` (bundle → scp → extract → py_compile → restart → verify).
Verify after deploy: `autopilot/status` endpoint, `journalctl -u sba-autopilot.service`.

---

## Current Error Logs (recent, journalctl sba-autopilot)

```
Aug 08 08:53  ImportError: cannot import name 'build_workspace_email_client'  <- crash-loop, FIXED
Aug 08 08:53  SBAMeetingManager.__init__() got an unexpected keyword arg 'email_client'  <- stale sba_meeting.py, FIXED
Aug 08 08:57  restarted with all 4 files deployed; NRestarts=0 since
Aug 08 09:02  pass_summary: emails_sent 0, no_email 619 (29 deferred to business hours)
Aug 08 09:39  pass_summary: emails_sent 0, no_email 618, 4 leads judged (auto repair Houston)
```

- No SMTP errors yet because no sends have happened (`send_failed: 0`).
- Leads ARE being judged each pass (Google Maps rotation active).
- Backfill chrome CDP errors are transient (Google throttle) — retries handle.

---

## Current Issue Being Fixed (DO NOT RESCAN THE REPO)

**Problem:** 640+ leads have no email, so no cold emails are being sent and the
lead-to-meeting pipeline is stalled at step 2.

**Root cause (FOUND):** `SBAWorkspaceRunner.run_all_once()` creates a fresh
`SBAAutopilot` per pass. The 24h enrichment cooldown (`_enriched_at`) lived
only in memory, so it reset every pass. Result: the same un-enrichable lead
(Curt Hinkle DDS) got retried every ~20 min, and the 12-slot per-pass
enrichment budget was burned on it, starving the other 640 leads.

**Fix (commit `0711677`, deployed 07:02 UTC):**
- `_enriched_at` now loads from / saves to `.sba_enrichment_state` (same
  pattern as `.sba_rotation_state`), so cooldown survives restarts.
- Per-lead enrichment ceiling 120s → 45s (`ENRICH_TIMEOUT_SECONDS`).
- Test infra: fixed stale async `find_leads_all` stub, isolated per-test state.
- 94 SBA tests pass (12 autopilot + 82 others).

**Proof it's working:** state file now tracks multiple leads per pass
(ids 468, 481, 488, 493 seen), not just Curt Hinkle.

**Still open:** enrichment finds emails slowly (Bing + site crawls). Until
`emails_sent > 0`, keep watching. If enrichment returns too little, next lever
is raising `SBA_MAX_ENRICH_PER_PASS` (currently 12) or adding more email
sources to `admin/tools/lead_enrichment.py`.

## Current Issue Being Fixed (second round — DO NOT RESCAN THE REPO)

**Problem (fixed `0c1352c`, deployed 07:19 UTC):** even after the cooldown fix,
`enrichment timed out` lines kept appearing (Curt Hinkle DDS, Houston Landscape
Pros). Root cause: `find_lead_email` had NO internal time budget. Worst case
per call: Bing 3 queries × 3 attempts × (15s + 2s) ≈ 150s, then per candidate
domain `_homepage_check` (2 × 10s) + `_crawl_domain` (5 pages × 2 schemes ×
12s) ≈ 140s. And `requests` read timeout is per-chunk, so a drip-feeding site
can hold one request for minutes — the 45s `asyncio.wait_for` cannot cancel a
thread, so the crawl kept running after the wrapper gave up.

**Fix:** `ENRICH_BUDGET_SECONDS` (38s, configurable, under the 45s wrapper) +
`_now/_expired/_remaining/_sleep` deadline helpers. Every request uses
`(min(3.05, remaining), remaining)` timeouts; loops abort the instant the
budget is exhausted. Verified: all requests hanging until their read timeout →
one enrichment finishes in 3.9s with a 4s budget; 12/12 autopilot tests pass.

---

## Recent Commits (this branch)

| Commit | What |
|---|---|
| `9e3e83e` | **crash-loop fix + junk email gate + workspace email identity** (current) |
| `4c6dc28` | prioritize enrichment-ready leads + backfill phone-match fix |
| `0c1352c` | enrichment internal 38s budget + shrinking timeouts |
| `0711677` | enrichment state persistence + 45s wrapper timeout |
| `87ff421` | leads `website` column migration (PGRST204 fix) |
| `aa38243` | email client `TAGS_SMTP_*` env fallback |
| `f3efb99` | repo cleanup: removed scratch files, updated .gitignore |
| `0b03900` | capture `website` from Maps, os import, settle 8s |

## Run Log

- 07:02 UTC — deployed `0711677`, autopilot restarted (new PID).
- 07:19 UTC — deployed `0c1352c` (internal 38s budget).
- 08:53 UTC — deployed `sba_email_client.py` fix (crash-loop import error).
- 08:57 UTC — deployed `sba_meeting.py`, `sba_biztypes.py`, `sba.py`; restarted
  autopilot; NRestarts=0 since.
- 09:02 UTC — clean pass (no_email 619, 29 deferred). Commit `9e3e83e`.
- 09:05 UTC — backfill relaunched with junk gate (pid 2367341), 668 leads.
- 09:39 UTC — pass judged 4 auto-repair Houston leads; DB 670 total, 31 emails.

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
- Supabase: **664/664 leads are `workspace_name = agency`**. No client workspace
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
