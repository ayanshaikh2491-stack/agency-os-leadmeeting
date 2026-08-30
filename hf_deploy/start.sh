#!/bin/bash
# R2 restore FIRST — restart pe ephemeral storage empty hota hai,
# R2 se PocketBase data + JSON stores wapas laate hain.
if [ -n "$R2_SYNC_BUCKET" ]; then
    /usr/local/bin/python /app/admin/hf_sync.py restore 2>/dev/null || true
fi

# PocketBase background start
/app/pocketbase serve --http=0.0.0.0:8090 --dir=/app/pb_data &

# R2 periodic sync background — har 5 min data R2 pe save
if [ -n "$R2_SYNC_BUCKET" ]; then
    (
        while true; do
            sleep 300
            /usr/local/bin/python /app/admin/hf_sync.py sync 2>/dev/null || true
        done
    ) &
fi

# FastAPI start (port $PORT HF Spaces hota hai)
exec uvicorn admin.main:app --host 0.0.0.0 --port 7860
