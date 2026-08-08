# STATE.md — Agency OS (SBA Lead-to-Meeting Pipeline)

> Purpose: one-page state so we never have to rescan the repo. Updated whenever
> the autopilot/agent status changes. Branch: `feat/sba-lead-to-meeting-pipeline`.

**Last updated:** 2026-08-08 12:50 IST (07:20 UTC)

---

## High Priority Tasks

1. **Get enrichment to actually fill emails** (blocking everything)
   - 643 leads have NO email, only 2 have one, `emails_sent: 0`.
   - Root cause was FIXED + deployed (`0711677`): per-pass instance reset the
     24h enrichment cooldown, so the same stuck lead was retried every pass.
   - Now state persists in `.sba_enrichment_state`; timeout cut 120s → 45s.
   - **Next action:** verify emails get found + `emails_sent` goes > 0. Watch
     enrichment lines in journal (new lead ids each pass = healthy).
2. **Curt Hinkle DDS enrichment wedged every pass** — FIXED (`0c1352c`, deployed 07:19 UTC)
   - Slow/drip-feeding domains ate the whole pass: no internal time budget,
     requests read-timeout is per-chunk (can hang minutes), and Bing retries
     alone could run ~150s. Enrichment now self-terminates within a 38s budget
     (under the 45s wrapper): per-request timeouts shrink with the remaining
     budget, connect capped at 3.05s.
   - **Next action:** next pass should show far fewer/no "enrichment timed out"
     lines; watch `no_email` shrink as enrichment actually completes.
3. **Lead finding returned 0 new leads for 3+ passes** (hvac Kansas City target)
   - May be a dedupe/rotation cycle, or the browser source is wedged. Check
     `new_leads_found` over the next few passes; if still 0, restart chrome/CDP.
4. **Memory pressure on EC2:** 1.9GiB total, ~618MiB available. OOM killed the
   box once (Aug 5). Swap (10G) is active. Do NOT add heavier workloads to EC2.
5. **Email send cap / Gmail daily limit** — once sends start, watch for 550s;
   backoff is 24h per recipient and is already implemented.

---

## Agency Agents Status (EC2: 18.213.66.136, t3.small)

| Agent / Service | Status | Notes |
|---|---|---|
| `api/health` | ok | version 0.1.0, `ceo_ready: true`, workspace_count: 2 |
| `sba.service` | active | backend API |
| `sba-autopilot.service` | active | 24/7 loop, ~20 min cadence, worker disabled |
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
Aug 08 06:00  enrichment timed out for Curt Hinkle DDS        <- pre-fix, same lead every pass
Aug 08 06:03  autopilot pass: emails_sent 0, no_email 639     <- starvation
Aug 08 06:26  autopilot pass: emails_sent 0, no_email 641
Aug 08 06:46  autopilot pass: emails_sent 0, no_email 641
Aug 08 07:04  enrichment timed out for Curt Hinkle DDS        <- state-persist fix, once/24h now
Aug 08 07:05  enrichment timed out for Houston Landscape Pros <- wedged ~45s
Aug 08 07:06  autopilot pass: emails_sent 0, no_email 643
07:19 UTC     deployed 0c1352c (internal 38s budget)          <- expect timeouts to stop here
```

- No SMTP errors yet because no sends have happened (`send_failed: 0`).
- `0 new leads found` is suspicious — see High Priority #3.
- Post-`0c1352c` passes pending (next ~20 min cycle); verify no new
  "enrichment timed out" lines and enrichment now returns "".

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
| `0c1352c` | **enrichment internal 38s budget + shrinking timeouts** (current fix) |
| `0711677` | enrichment state persistence + 45s wrapper timeout |
| `87ff421` | leads `website` column migration (PGRST204 fix) |
| `aa38243` | email client `TAGS_SMTP_*` env fallback |
| `f3efb99` | repo cleanup: removed scratch files, updated .gitignore |
| `0b03900` | capture `website` from Maps, os import, settle 8s |

## Run Log

- 07:02 UTC — deployed `0711677`, autopilot restarted (new PID).
- 07:06 UTC — pass shows `no_email: 643`; enrichment now hitting different leads.
- 07:19 UTC — deployed `0c1352c` (internal 38s budget); next passes should have
  no "enrichment timed out" lines.
