"""HF Spaces ephemeral storage survival — PocketBase data sync to/from Cloudflare R2.

Usage:
    python -m admin.hf_sync sync    # upload pb_data + JSON stores to R2
    python -m admin.hf_sync restore # download from R2 into pb_data (startup pe)

Env vars (HF Space Settings mein set karo):
    R2_SYNC_BUCKET   — bucket name (required; agar unset, no-op)
    R2_ENDPOINT      — https://<account>.r2.cloudflarestorage.com
    R2_ACCESS_KEY    — R2 access key id
    R2_SECRET_KEY    — R2 secret
    HF_SYNC_PREFIX   — default "agency-os-backup"

Local-first: SQLite WAL checkpoint sync se partial file corruption avoid hota hai.
"""

from __future__ import annotations

import os
import sqlite3
import tempfile
from pathlib import Path

PREFIX = os.getenv("HF_SYNC_PREFIX", "agency-os-backup")
BUCKET = os.getenv("R2_SYNC_BUCKET", "")
PB_DIR = Path(os.getenv("PB_DATA_DIR", "/app/pb_data"))

# JSON file stores jo PB ke sath mirror hote hain (workspace data)
_EXTRA_DIRS = [
    Path("admin/data"),
    Path("data"),
]


def _client():
    if not BUCKET:
        return None
    import boto3  # lazy import: sync ke liye hi chahiye

    return boto3.client(
        "s3",
        endpoint_url=os.getenv("R2_ENDPOINT", ""),
        aws_access_key_id=os.getenv("R2_ACCESS_KEY", ""),
        aws_secret_access_key=os.getenv("R2_SECRET_KEY", ""),
    )


def _checkpoint(pb_dir: Path) -> None:
    """SQLite WAL checkpoint — .db file self-contained ban jata hai upload se pehle."""
    for db in pb_dir.glob("*.db"):
        try:
            conn = sqlite3.connect(db)
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
            conn.close()
        except sqlite3.Error:
            pass


def sync() -> int:
    """pb_data + JSON stores → R2 upload. Return: files uploaded."""
    s3 = _client()
    if s3 is None:
        print("[hf_sync] R2_SYNC_BUCKET unset — skipping sync")
        return 0

    PB_DIR.mkdir(parents=True, exist_ok=True)
    _checkpoint(PB_DIR)

    count = 0
    for path in PB_DIR.rglob("*"):
        if path.is_file():
            key = f"{PREFIX}/pb_data/{path.relative_to(PB_DIR).as_posix()}"
            s3.upload_file(str(path), BUCKET, key)
            count += 1

    for extra in _EXTRA_DIRS:
        if extra.exists():
            for path in extra.rglob("*"):
                if path.is_file():
                    key = f"{PREFIX}/files/{extra.name}/{path.relative_to(extra).as_posix()}"
                    s3.upload_file(str(path), BUCKET, key)
                    count += 1

    print(f"[hf_sync] uploaded {count} files to s3://{BUCKET}/{PREFIX}")
    return count


def restore() -> int:
    """R2 → pb_data + JSON stores. Startup pe call karo. Return: files restored."""
    s3 = _client()
    if s3 is None:
        print("[hf_sync] R2_SYNC_BUCKET unset — skipping restore")
        return 0

    PB_DIR.mkdir(parents=True, exist_ok=True)
    paginator = s3.get_paginator("list_objects_v2")

    count = 0
    for page in paginator.paginate(Bucket=BUCKET, Prefix=f"{PREFIX}/"):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            rel = key.removeprefix(f"{PREFIX}/")

            if rel.startswith("pb_data/"):
                target = PB_DIR / rel.removeprefix("pb_data/")
            elif rel.startswith("files/"):
                parts = rel.removeprefix("files/").split("/", 1)
                if len(parts) != 2:
                    continue
                target = Path(parts[0]) / parts[1]
            else:
                continue

            target.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                s3.download_fileobj(BUCKET, key, tmp)
                os.replace(tmp.name, target)
            count += 1

    print(f"[hf_sync] restored {count} files from s3://{BUCKET}/{PREFIX}")
    return count


if __name__ == "__main__":
    import sys

    cmd = sys.argv[1] if len(sys.argv) > 1 else "sync"
    if cmd == "sync":
        sync()
    elif cmd == "restore":
        restore()
    else:
        print("usage: python -m admin.hf_sync [sync|restore]")
