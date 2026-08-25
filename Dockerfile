# TAGS Agency OS — AWS-light container image
#
# Designed to run as a single process on a small EC2 (or any container host):
#   - Default SQLite persistence (no external DB required)
#   - One uvicorn process serving admin.main:app
#   - Configured entirely via environment variables (see .env.example)
#
# Build:
#   docker build -t tags-agency-os .
# Run:
#   docker run -p 9002:9002 --env-file .env tags-agency-os

FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first (better layer caching).
COPY admin/requirements.txt /app/admin/requirements.txt
RUN pip install -r /app/admin/requirements.txt

# Copy the application source.
COPY . /app

# SQLite data dir lives here; mount a volume for durable persistence.
ENV TAGS_DATA_DIR=/app/data
ENV ADMIN_HOST=0.0.0.0
ENV ADMIN_PORT=9002
RUN mkdir -p /app/data

EXPOSE 9002

# Single-process server. Override ADMIN_HOST/ADMIN_PORT via env.
CMD ["python", "-m", "admin.main"]
