# HANDOFF — TAGS Agency OS (Backend + EC2 Deploy)

**Date:** 2026-08-22  |  **Status:** DEPLOYED & LIVE on EC2 — continue from here tomorrow.

> Kal subah seedha isi state se kaam shuru karna. Neeche sab hai: kya deploy hua,
> kahan hai, kaise update karna hai, kya verify hua, aur kya next hai.
> 6 lead-scraper files AUR agency-frontend submodule — INHE MAT CHHEDNA.

---

## 1. Aaj kya hua (recap)

Phase 1-3 backend complete + EC2 deploy complete. CEO (Michael, LangGraph)
orchestrator-only; dynamic user-added agents (Munder-style); CEO fan-out to
built-in + custom agents; agents think before acting; AWS-light single-process.

Commits (branch `feat/sba-lead-to-meeting-pipeline`):
- `47fc16d` feat(agency): dynamic user-added agents (registry + worker bridge + CRUD API)
- `4be51d1` feat(agency): multi-agent orchestration (CEO fan-out to built-in + custom)
- `d2ba350` chore(deploy): AWS-light deploy artifacts (Dockerfile, Procfile, .dockerignore, DEPLOY.md)
- `03f3eeb` fix(agents): social/website tool dispatchers tolerate injected delegation kwargs

## 2. EC2 deploy — live details

| Item | Value |
|------|-------|
| Host | `ubuntu@18.213.66.136` (public IP `18.213.66.136`) |
| SSH key | `int_ec2.pem` (in working dir `C:\Users\TAUSHEF\Downloads\int`) |
| Our app dir | `/opt/tags-agency-os` |
| Our port | **9002** (Uvicorn `0.0.0.0:9002`) |
| Our service | `tags-agency.service` (systemd, auto-restart, log `/var/log/tags-agency.log`) |
| DB (ORM/SBA) | `data/tags_agency.db` (SQLite) |
| DB (workspace/custom agents) | `tags_agency_workspace.db` (SQLite, has `custom_agents` table) |
| Existing live app | `sba-backend` on **port 8000** — SEPARATE, untouched, still running |
| Python | 3.12 venv at `/opt/tags-agency-os/venv` |

Health: `curl http://18.213.66.136:9002/api/health` → `{"status":"ok","ceo_ready":true,...}`

## 3. Verified working live (real EC2)

- `GET /api/health` → ok, ceo_ready true, workspace_count 2 ✅
- `POST /api/agents/custom` → creates dynamic agent, PERSISTS to SQLite
  (`custom_agents` table had 2 rows from live calls: SmokeBot, QA2) ✅
- `POST /api/ceo/run` → CEO fans out to ALL 8 agents (7 built-in + custom),
  real LLM calls return 200 OK, NO dispatch errors after the `03f3eeb` fix ✅

## 4. Bug fixes done during deploy (commit `03f3eeb`)

- **Root cause:** `workers.py:_parse_brief` injects `{"workspace_id":..., "__brief":...}`
  into every tool call, but social/website tool funcs (e.g. `content_calendar`)
  don't accept those kwargs → TypeError failed the CEO fan-out for those agents.
- **Fix:** `execute_social_tool` and `execute_website_tool` now filter `args` to each
  tool's declared signature (`inspect.signature`) before calling.
- **Missing deps added to `admin/requirements.txt` + installed on EC2 venv:**
  `aiosqlite`, `python-multipart`, `dnspython`, `bs4`, `lxml`, `pandas`, `numpy`,
  `openpyxl`, `Pillow`, `aiohttp`, `markdown`, `jinja2`, `boto3`, `python-docx`, `PyMuPDF`.

## 5. KNOWN behavior (not a bug)

- **CEO run is SLOW (~5 min).** The SBA agent runs its full email-enrichment +
  send pipeline and the website agent launches Chrome/Playwright. This is the
  existing `admin` codebase's design, not a deploy defect. Each agent is
  failure-isolated (one slow/failing agent doesn't block the rest).
- If a curl to `/api/ceo/run` returns empty, it just means the 180-300s client
  timeout elapsed before the server finished the synchronous fan-out. The server
  keeps processing; check `/var/log/tags-agency.log`.

## 6. How to UPDATE the EC2 deploy (when code changes)

```bat
REM 1. On local Windows, from C:\Users\TAUSHEF\Downloads\int:
git bundle create _deploy.bundle HEAD
scp -i int_ec2.pem -o StrictHostKeyChecking=no -o BatchMode=yes _deploy.bundle ubuntu@18.213.66.136:/tmp/tags_deploy.bundle

REM 2. On EC2 (ssh), pull + restart. .env and data/ are UNTRACKED so they survive:
cd /opt/tags-agency-os
git fetch /tmp/tags_deploy.bundle HEAD
git reset --hard FETCH_HEAD
sudo systemctl restart tags-agency.service
```

**SSH gotcha (important for tomorrow):** the remote login shell has `IFS` unset,
so multi-word remote commands get mangled ("echo SSH_OK" treated as one command).
Workaround that WORKS: write a `.sh` script (LF line-endings!), then
`type script.sh | ssh -i int_ec2.pem -o BatchMode=yes ubuntu@18.213.66.136 bash`.
Single-token commands (e.g. `whoami`) also work directly.

**2026-08-23 note:** external inbound on 9002 was NOT open in SG `sg-02b87bc26027dc457`
(only 80/443/22/8000/3001-3004/4000/4007/4008/8050/8055/8090 were). Opened via
`AuthorizeSecurityGroupIngress` (rule `sgr-01dbacef76e41c4e3`, tcp 9002, 0.0.0.0/0).
If external `curl` returns empty again, re-check SG inbound before assuming app died.

## 7.5 EC2 instance facts

- Instance ID `i-09a4dceddec646417`, region `us-east-1`, account `176980002493`
- Security group: `sg-02b87bc26027dc457` (inbound 9002 now open)

## 7. What's NOT done / NEXT (user decides)

- [ ] Munder-style UI (agent gallery + CEO command console + live results)
- [ ] Put backend behind a domain / reverse proxy (currently raw IP:9002).
      NOTE 2026-08-25: office floor ab WS use NAHI karta - ye same-origin
      /api/ceo/floor ko 3s poll karta hai (Vercel proxy -> EC2), jo HTTPS pe
      bhi chalta hai aur PROD VERIFIED hai. Purana ws:// endpoint backend mein
      tha hi nahi. Avatars activity-driven hain: working=laptop/desk,
      coding(website)=desktop monitor, idle=cafeteria coffee, error=red !
- [x] Open EC2 security-group inbound for 9002 (DONE 2026-08-23: rule `sgr-01dbacef76e41c4e3`, SG `sg-02b87bc26027dc457`, CIDR `0.0.0.0/0`)
- [ ] Push commits to `origin` (currently 4 commits ahead of origin, not pushed)

## 8. Do NOT touch

- The 6 staged lead-scraper files (in `admin/...`, lead pipeline).
- The `agency-frontend` git submodule.
- The live `sba-backend` on port 8000 (separate service, don't restart/kill it).

## 9. Quick re-verify tomorrow

```sh
curl -s http://18.213.66.136:9002/api/health
curl -s -X POST http://18.213.66.136:9002/api/agents/custom -H 'Content-Type: application/json' -d '{"name":"X","role":"qa","system_prompt":"hi"}'
sudo systemctl status tags-agency.service
```
