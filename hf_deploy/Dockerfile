FROM python:3.11-slim

# PocketBase download + system deps
RUN apt-get update && apt-get install -y --no-install-recommends wget sqlite3 ca-certificates && \
    rm -rf /var/lib/apt/lists/* && \
    wget -q https://github.com/pocketbase/pocketbase/releases/download/v0.23.0/pocketbase-linux-amd64 -O /app/pocketbase && \
    chmod +x /app/pocketbase

WORKDIR /app

# Python deps pehle (cache-friendly)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Backend code copy (sirf code — data R2 se restore hota hai)
COPY admin /app/admin
RUN mkdir -p /app/admin/data /app/pb_data

# HF Spaces: non-root user REQUIRED hai
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# HF Spaces: README.md metadata ke port se match — 7860
ENV PB_PORT=8090 API_PORT=7860

# Startup script: R2 restore → PocketBase → sync loop → FastAPI
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

EXPOSE 7860

CMD ["/app/start.sh"]
