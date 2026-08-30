# Agency OS on Hugging Face Spaces — Free 16GB RAM Backend

HF Spaces ka free CPU Basic tier: **2 vCPU + 16GB RAM**, forever free, no credit card.
Ek hi catch hai: **storage ephemeral** (restart pe wipe). Is setup ne wo problem R2 sync se solve ki hai.

## Files

| File | Kaam |
|------|------|
| `hf_deploy/Dockerfile` | HF Spaces Docker build — PocketBase + FastAPI |
| `hf_deploy/start.sh` | R2 restore → PocketBase → R2 sync loop → FastAPI |
| `admin/hf_sync.py` | PocketBase + JSON stores ko Cloudflare R2 pe save/restore |

## Deploy Steps

1. **Hugging Face account** banao (free, no CC): huggingface.co
2. **New Space** → name: `agency-os` → SDK: **Docker** → visibility: Public ya Private
3. **Repo upload** (git se):
   ```bash
   git clone https://huggingface.co/spaces/<username>/agency-os
   cd agency-os
   # hf_deploy/* ko root pe copy karo (Dockerfile + start.sh root pe chahiye)
   cp ../hf_deploy/Dockerfile ../hf_deploy/start.sh .
   cp ../admin/requirements.txt .
   cp -r ../admin admin
   git add . && git commit -m "deploy agency-os" && git push
   ```
4. **R2 bucket** banao (data survival ke liye, free 10GB):
   - Cloudflare dashboard → R2 → Create bucket: `agency-os-backup`
   - R2 → Manage API Tokens → Create: Object Read & Write → keys copy karo
5. **HF Space Settings → Variables and secrets** mein set karo:
   ```
   R2_SYNC_BUCKET   = agency-os-backup
   R2_ENDPOINT      = https://<account-id>.r2.cloudflarestorage.com
   R2_ACCESS_KEY    = <r2 access key>
   R2_SECRET_KEY    = <r2 secret>        ← "Secret" mark karo
   POCKETBASE_URL   = http://127.0.0.1:8090
   OPENAI_API_KEY   = <zen/llm key>     ← "Secret" mark karo
   ```
6. **Space restart** — logs mein `[hf_sync] restored N files` dikhega

## URLs

| Service | URL |
|---------|-----|
| FastAPI backend | `https://<username>-agency-os.hf.space/api/health` |
| PocketBase admin | `https://<username>-agency-os.hf.space:8090/_/` (nahi—to nginx/streamlit proxy needed) |
| PB admin (proxy ke bina) | HF sirf 7860 expose karta hai — PB admin local SSH se, ya admin/data pe filesystem se |

NOTE: HF Spaces sirf **7860** port expose karta hai. PocketBase (8090) internal rahega —
FastAPI se hi reach hota hai (`POCKETBASE_URL=http://127.0.0.1:8090`), jo exactly humara pattern hai.

## Keep-Alive (sleep avoid)

HF free Spaces **48 hours inactivity** pe sleep karte hain. Free fix:
- cron-job.org (free) → har 30 min → `GET https://<user>-agency-os.hf.space/api/health`

## Data Survival (R2 Sync)

```
Restart/Rebuild → start.sh → hf_sync.py restore → pb_data wapas
Har 5 min → hf_sync.py sync → pb_data R2 pe save
```

PocketBase SQLite (WAL checkpoint ke sath) + `admin/data` + `data` JSON stores — sab R2 pe safe.

## Local Test (deploy se pehle)

```bash
cd hf_deploy
docker build -t agency-os-hf .
docker run -p 7860:7860 -e R2_SYNC_BUCKET=agency-os-backup \
  -e R2_ENDPOINT=... -e R2_ACCESS_KEY=... -e R2_SECRET_KEY=... agency-os-hf
curl http://localhost:7860/api/health
```

## Cost

| Item | Cost |
|------|------|
| HF Spaces CPU Basic | $0 forever |
| Cloudflare R2 (10GB) | $0 forever |
| cron-job.org pinger | $0 |
| **Total** | **$0/month** |
