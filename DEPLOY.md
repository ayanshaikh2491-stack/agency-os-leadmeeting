# Deploy — AWS-light

Single process, SQLite by default. No external database, no always-on heavy
services. Intended for a small EC2 (t3.small / t4g) or any container host.

## What runs
- `python -m admin.main` → uvicorn serving `admin.main:app` on
  `ADMIN_HOST` (default `0.0.0.0`) + `ADMIN_PORT` (default `9002`).
- All persistence (agent registry, workspace data, knowledge) lives in SQLite
  under `TAGS_DATA_DIR` (default `./data`). Mount a volume there for durability.

## Option A — Docker (recommended)
```bash
# 1. Build
docker build -t tags-agency-os .

# 2. Run (env from a file; see .env.example for the full key list)
docker run -d --name tags-os -p 9002:9002 \
  -v tags-data:/app/data --env-file .env tags-agency-os

# 3. Health
curl http://localhost:9002/api/health
```
- Dependencies install from `admin/requirements.txt` (incl. Playwright/Chromium
  for the SBA browser agent — the install is best-effort and won't fail the build).
- `.dockerignore` keeps the image small (excludes `agency-frontend`, scratch
  files, `.git`, `*.pem`, etc.).

## Option B — systemd on a bare EC2 (Ubuntu/RHEL)
```ini
# /etc/systemd/system/tags-agency.service
[Unit]
Description=TAGS Agency OS
After=network.target

[Service]
WorkingDirectory=/opt/tags-agency-os
EnvironmentFile=/opt/tags-agency-os/.env
ExecStart=/usr/bin/python3 -m admin.main
Restart=always
User=ubuntu

[Install]
WantedBy=multi-user.target
```
```bash
sudo cp .env /opt/tags-agency-os/.env
sudo systemctl daemon-reload && sudo systemctl enable --now tags-agency
```

## Option C — Heroku-style PaaS
The `Procfile` declares `web: python -m admin.main`. Connect the repo and set
config vars from `.env.example`.

## Configuration
All config is via environment variables — see `.env.example`:
- `ADMIN_HOST` / `ADMIN_PORT` — server bind.
- `TAGS_DATA_DIR` — SQLite + data directory (mount a volume).
- Model keys: `GROQ_API_KEY` (free default), `WORKSPACE_API_KEY`,
  `WORKSPACE_AGENT_MODEL`, `AGENCY_CEO_MODEL`, etc. (see `.env.example`).
- `DATABASE_URL` — defaults to SQLite; override only if you want Postgres.

## Ports
- Inbound: `9002/tcp` (the API). Open it in the EC2 security group.
- The frontend (`agency-frontend`, separate Vercel app) proxies to this backend.
