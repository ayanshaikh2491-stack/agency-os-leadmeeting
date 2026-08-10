# DB PERSISTENCE FIX — 2026-08-02

## Root cause
`/home/ubuntu/sba-backend/.env` line 27 was COMMENTED OUT:
```
# DATABASE_URL=postgresql+asyncpg://username:pass@localhost:5432/tags_agency
```
So `admin/database.py` could never connect → silent fallback to in-memory store
(`admin/agency/sba_store.py`) → ALL data (leads, meetings, statuses) lost on restart.

## What was done (server, self-hosted setup)
1. Created role + DB in SYSTEM postgres 16 (127.0.0.1:5432 — NOT the supabase container):
   - `CREATE ROLE letta LOGIN PASSWORD 'SBA_letta_2026'`
   - `CREATE DATABASE tags_agency OWNER letta`
2. Uncommented + fixed `.env`:
   - `DATABASE_URL=postgresql+asyncpg://letta:SBA_letta_2026@127.0.0.1:5432/tags_agency`
   - Backup: `.env.bak`
3. App auto-created tables on first connect: `leads`, `meetings`, `handoffs` (owner letta)

## Verified (all PASSED)
- `WRITE OK` via asyncpg test
- Service restart → test lead `388e0c3b07cb` STILL there, meeting count STILL 1
- 324 leads load from Supabase bridge at startup (`load_leads_from_supabase` → 324 rows)
- Test lead deleted after verification; DB clean (0 local leads, bridge gives 324)

## Notes
- Two postgres servers exist: system PG 16 (127.0.0.1:5432, used by app) and
  supabase container (host 5433 = pgbouncer, needs SNI; container not host-mapped).
  Supabase container holds the 324 source leads in `public.leads` (postgres db).
- New/updated leads + meetings are now PERSISTED in local `tags_agency` DB.
- Gmail creds (`SBA_OWNER_EMAIL` + App Password) still needed for real email sends.
