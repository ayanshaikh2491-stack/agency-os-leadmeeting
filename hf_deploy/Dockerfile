FROM python:3.11-slim

# PocketBase download + system deps
RUN apt-get update && apt-get install -y wget sqlite3 ca-certificates && \
    rm -rf /var/lib/apt/lists/* && \
    wget -q https://github.com/pocketbase/pocketbase/releases/download/v0.23.0/pocketbase-linux-amd64 -O /app/pocketbase && \
    chmod +x /app/pocketbase

WORKDIR /app

# Python deps pehle (cache-friendly)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Backend code copy (admin/ ko /app/admin banata hai)
COPY admin /app/admin

# HF Spaces port env
ENV PB_PORT=8090
ENV API_PORT=7860

# Startup script: PocketBase + FastAPI dono
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

EXPOSE 7860

CMD ["/app/start.sh"]
