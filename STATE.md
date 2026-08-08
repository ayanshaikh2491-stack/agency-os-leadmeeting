# STATE.md — Agency OS (SBA Lead-to-Meeting Pipeline)

> Purpose: one-page state so we never have to rescan the repo. Updated whenever
> the autopilot/agent status changes. Branch: `feat/sba-lead-to-meeting-pipeline`.

**Last updated:** 2026-08-08 19:40 IST (14:10 UTC)

---

## High Priority Tasks

1. **Autopilot healthy — 50+ passes, NRestarts=0** — DONE
   - Deployed `979ef71` (12:22 UTC): generic first-party email prefix fix (see #3).
   - Restart clean (12:22:48 UTC), fresh pass at 12:25 UTC complete normally.
2. **Website backfill COMPLETE** — DONE
   - Backfill finished 10:30 UTC: 670 leads, 487 no-website, 63 with email.
   - Only orphaned chrome (port 9252) remains; harmless.
3. **Enrichment yield fix DEPLOYED (`979ef71`, 12:22 UTC)** — ROOT CAUSE FOUND + RE-ENRICH DONE
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
     (previously empty).
4. **Re-enrichment batch COMPLETE (12:39 UTC)** — DONE
   - 133 website-having no-email leads retried with fixed gate (REST-based,
     venv, bypassed 24h cooldown).
   - **RESULT: found=44, skipped=1, failed=0.** All 44 emails patched to
     Supabase with provenance (mostly `own_domain`/`homepage`, 1 consumer).
     Examples: info@beyondwow.com, info@coolmenow.com, service@nicksplumbing.com,
     info@roofsquad.com, contact@dfw-roofinginc.com.
   - Expected no_email now ~541 (down from 585). Verify via Supabase count.
5. **LEADS ARE FLOWING** — multi-source, NOT just Google Maps
   - Autopilot `_find_new_leads` → `find_leads_all` loops **5 sources**:
     google_maps, yelp, yellowpages, bing_maps, facebook_pages.
   - DB 671 leads (latest). Enrichment state tracks 156 leads; ~60 tried in 2h.
6. **Email sends — still 0 today, 3 total historical**
   - 62 leads deferred to business hours (it is 8:55 AM CDT now; sends start
     ~14:00 UTC = 9 AM CDT, cap 30/day). Watch `emails_sent` after 14:00 UTC.
7. **Memory pressure on EC2:** 1.9GiB total, swap active. Do NOT add heavier
   workloads to EC2.
8. **Email send cap / Gmail daily limit** — once sends start, watch for 550s;
   backoff is 24h per recipient and is already implemented.

---

## Loop Engineering Setup — DONE (13:50 UTC)

- **7 loop skills installed to system** `C:\Users\TAUSHEF\.jcode\skills\`:
  `/install-loop`, `/loop-triage`, `/loop-verifier`, `/minimal-fix`,
  `/loop-budget`, `/loop-constraints`, `/budget-negotiator`
  (from cobusgreyling/loop-engineering, cloned 12:50 UTC, verified loaded via
  skill reload — 242 skills).
- **`loop doctor` on repo:** score **100 / L3** (was L2). Added:
  - `.claude/agents/loop-verifier.md` (maker/checker split agent)
  - `docs/safety.md` (path denylist, auto-merge L1/L2/L3 policy, MCP scopes,
    escalation, budget)
  - Commit `a8466f0`.
- **Not enabled (needs human opt-in):** Foundry harness (`--with-foundry`),
  GitHub issue/PR templates + workflows, MCP usage doc.
- User workflow: jab bhi `/loop-*` command ya "loop se kaam kar" bole, skills
  use hoti hain.

---

## Two-Account Migration (IN PROGRESS — 15:55 UTC)

**Why:** EC2 #1 (t3.small, 2GB) is at 81% disk (31G/38G), RAM tight (1.2G/1.9G used).
Supabase stack (13 containers, ~11GB docker images, ~400MB RAM) + Rallly (2 containers) are the heaviest.

**New AWS account:** `301556368065` (Umer, IN) — profile `aws2`, logged in via `aws login` (root), region us-east-1, billing view HEALTHY. Free tier (15 Jul 2025+ rule): **t3.small (2GB) IS free-tier eligible** + $100 sign-up credit. Old account `default` (176980002493, t3.small 2GB, 40GB) untouched + `~/.aws/credentials.bak`.

**BLOCKER: EC2 service not activated yet** (`OptInRequired` on describe-instances/regions/AMI — signup complete but AWS service activation pending, 15min-24h). Retry `deploy/_aws_newacct_check.ps1` until it clears.

**Migration plan (when EC2 activates):**
1. Launch t3.small (2GB) Ubuntu 24.04, 40GB gp3, key `ec2-key.pem` in account `aws2`.
2. Run `deploy/migrate_supabase.sh <old_ip>` on new instance → installs docker, rsyncs supabase+rallly configs, pg_dump from old, restores, starts both.
3. Point backend to new Supabase URL in `/home/ubuntu/sba-backend/.env` (SUPABASE_URL/KEY), restart `sba.service`.
4. Stop + remove supabase/rallly containers + volumes on OLD EC2 → frees ~11GB disk + ~400MB RAM.
5. Verify: `/api/health`, autopilot pass, Supabase count (671 leads), Rallly login.

**Supabase data locations (OLD EC2):** DB bind mount `/home/ubuntu/supabase/docker/volumes/db/data` (NOT a docker volume), config volume `supabase_db-config`, deno cache `supabase_deno-cache`. Rallly: `/home/ubuntu/rallly`, volume `rallly_db-data`, postgres on 5450, app on 3001. Backend env: `SUPABASE_URL=http://localhost:8000` (kong), `SUPABASE_SERVICE_KEY` live.

---

## Agency Agents Status (EC2: 18.213.66.136, t3.small)

**Framework: LangGraph** (crewai REMOVED `81cc807` — `crewai-repo/` deleted, .gitignore updated).
All agents expose FastAPI routes under `/api/*`; only SBA autopilot runs 24/7 as a
systemd daemon — the others are on-demand (API-driven, no scheduler daemon).

| Agent | Code | LangGraph? | API routes | Live status |
|---|---|---|---|---|
| **SBA autopilot** | `sba_autopilot.py` | `langgraph_sba.py` (SBAGraphState) | `/api/sba/*` | ✅ **running 24/7** (systemd `sba-autopilot.service`), ~20min cadence, NRestarts=0 |
| **CEO agent** | `ceo.py` → `AgencyCEO` | ✅ `build_ceo_graph()` (call_llm→run_tools→finalize) | `/api/ceo/chat`, `/handoff/receive`, `parallel-blast`, `review-output`, `route-error`, `generate-report` | ✅ graph builds OK, 4 nodes; **now Supabase-checkpointed** (`get_checkpointer("Agency","ceo")` fallback MemorySaver) + real `conversation_id` threading; on-demand (no daemon) |
| **Content agent** | `content_agent.py` → `AgencyContentAgent` | – (class-based) | `/api/content/init`, `/discover-brand`, `/status/{ws}` | ✅ importable + store present (`data/workspace_content_agents/ws_test.json`); on-demand |
| **SEO agent** | `seo_skills.py`, `seo_store.py` + `tools/seo_tools.py` | – | `/api/seo/chat`, `/audit`, `/audits` | ✅ importable; on-demand |
| **Social agent** | `social_skills.py` + `tools/social_tools.py` | – | `/api/social/chat`, `/calendar`, `/hashtags` | ✅ tokens store (`data/social_tokens/` 1/default/test); on-demand |
| **Website agent** | `website_skills.py` + `tools/website_tools.py` | – | `/api/website/chat`, `/analyze`, `/performance` | ✅ importable; on-demand |
| **Ads agent** | `tools/ads_tools.py` + `ads_api_client.py` | – | `/api/ads/status`, `/tools`, `/campaign-strategy` | ✅ importable; on-demand |
| **Swarm** | `swarm.py` | – | `/api/swarm/agents/add`, `/tasks/assign`, `/run` | ✅ importable; on-demand |
| **Orchestrator** | `orchestrator.py` | – (functions) | `/api/orch/workspace`, `/workspaces` | ✅ importable; on-demand |
| **Analytics** | routes only | – | `/api/analytics/status`, `/weekly-report` | ✅ on-demand |
| **Workflows** | routes only | – | `/api/workflows/*` | ✅ on-demand |
| **Agent aliases** | `routes/agent_aliases.py` | – | `/api/agents`, `/api/agents/{id}/chat`, `/seo-engine` | ✅ on-demand |

**Running services (systemd):**
| Service | Status | Notes |
|---|---|---|
| `sba.service` | active | backend API (all /api routes) |
| `sba-autopilot.service` | active | 24/7 SBA loop, ~20 min cadence, NRestarts=0 |
| `sba-chrome.service` | active | Chrome daemon for browser automation (1d19h uptime) |

**Other systemd agents:** NONE — no daemon runs CEO/content/SEO/social/website/ads.
They are API-on-demand only. A scheduler daemon is a future option (currently on-demand is the design).

**Email sends LIVE (13:19-13:20 UTC, first real sends!):** 12 emails sent to
re-enriched leads (info@flamingolandscapes.com, info@electricianatl.com,
info@primeroofrepairtampa.com, rainierroofingllc@hotmail.com, yosef@orlandoevergreen.com,
info@idealgardensorl.com, wayne@wayneslawnservice.com, info@hancocklandscape.com,
taylorlandscapingky@gmail.com, info@myersla.com, bladerunners1999@aol.com, +1).
Pass 13:25 summary: `emails_sent: 12, send_failed: 0, no_email: 540, deferred: 98`.
Pass 14:02: `emails_sent: 0` (cap reached for the day? watch). `reply_understood`
event seen 13:43 (a reply was processed).

| API health | ok | version 0.1.0, `ceo_ready: true`, workspace_count: 2 |
| Email client (`SBAEmailClient`) | enabled: True | creds live on EC2 (.env), code falls back to `TAGS_SMTP_*` |
| Supabase (docker) | running | 671 leads, ~541 no-email (after 44 re-enriched), ~480 no-website |
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
Aug 08 12:39  re-enrichment batch: found=44 emails (own_domain/homepage), patched to Supabase
Aug 08 13:50  loop engineering setup: skills installed + doctor 100/L3 + verifier agent + safety.md
```

- No SMTP errors yet because no sends have happened (`send_failed: 0`).
- Leads ARE being judged each pass (Google Maps rotation active).
- `meetings` + `email_sends` tables do NOT exist in Supabase (PGRST205 when
  probed) — meetings are stored locally in `sba_store` SQLite in-memory; a
  Supabase meetings table may be a future hardening step.

---

## Current Issue Being Fixed (DO NOT RESCAN THE REPO)

**Problem (fixed `979ef71`, deployed 12:22 UTC, re-enrichment DONE 12:39 UTC):**
604 leads had no email, so the pipeline stalled at step 2. Root cause found in
the enrichment VALIDITY GATE, not the crawl: generic first-party prefixes
(info@/contact@/office@) were unconditionally rejected even when the address
came from the business's own verified page. 124 leads HAVE websites; many
expose exactly such addresses.

**Fix:** prefix lists split into generic (verified-only) vs hard-junk (always),
in both `lead_enrichment.py` and `sba_autopilot.py`. Provenance
consumer/own_domain/homepage now implies "verified first-party" and unlocks
generic prefixes; unverified scrapes still reject them.

**Proof:** `find_lead_email("Beyond Wow Plumbing & Drains", ..., site=beyondwow.com)`
now returns `info@beyondwow.com` (own_domain). Re-enrichment of the 133
website leads found **44 emails**, all patched to Supabase.

**Still open:** (a) ~480 leads with no website need Bing-based enrichment
(slower, lower yield); (b) 403/Cloudflare/JS-rendered sites
(papermoonpainting, johnmooreservices, texasqualityplumbing) need a headless
browser for email extraction — NOT on EC2 (memory); (c) sends start ~14:00 UTC
— watch `emails_sent` and Gmail 550s.

---

## Recent Commits (this branch)

| Commit | What |
|---|---|
| `6bd88f5` | **CEO checkpointing: Supabase-backed cross-session memory + real conversation_id** (get_checkpointer("Agency","ceo"), fallback MemorySaver; tests 7 passed) |
| `a8466f0` | loop engineering: verifier agent + safety policy (doctor 100/L3) (current) |
| `aee18a7` | docs: STATE.md update after prefix fix deploy |
| `979ef71` | **generic first-party prefix fix (enrichment yield)** |
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
- 12:39 UTC — re-enrichment DONE: **found=44 emails** (skipped=1, failed=0),
  all patched to Supabase with provenance. no_email ~541.
- 12:40 UTC — Supabase verify script prepared (ran remotely via venv).
- 13:50 UTC — loop-engineering setup: 7 skills installed to system, `loop
  doctor` score 100/L3, verifier agent + safety.md committed (`a8466f0`).

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
