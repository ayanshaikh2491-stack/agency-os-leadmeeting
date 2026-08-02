import base64, hashlib, hmac, json, os, secrets

def rand_bytes(n):
    return os.urandom(n)

def b64u(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

def make_jwt(secret: str, role: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"role": role, "iss": "supabase-demo", "iat": 1641769200, "exp": 1799535600}
    h = b64u(json.dumps(header, separators=(",", ":")).encode())
    p = b64u(json.dumps(payload, separators=(",", ":")).encode())
    sig = hmac.new(secret.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
    return f"{h}.{p}.{b64u(sig)}"

jwt_secret = b64u(rand_bytes(48))          # >=32 chars
postgres_pw = b64u(rand_bytes(32)) + "aB1!"  # long & strong
anon = make_jwt(jwt_secret, "anon")
service = make_jwt(jwt_secret, "service_role")

env = f"""# Generated for TAGS Agency leads scraper - self-hosted Supabase on EC2
COMPOSE_FILE=docker-compose.yml

# Postgres
POSTGRES_PASSWORD={postgres_pw}

# Legacy symmetric HS256 key
JWT_SECRET={jwt_secret}
ANON_KEY={anon}
SERVICE_ROLE_KEY={service}

# Asymmetric keys (optional - not used)
SUPABASE_PUBLISHABLE_KEY=
SUPABASE_SECRET_KEY=
JWT_KEYS=
JWT_JWKS=

# Dashboard access
DASHBOARD_USERNAME=admin
DASHBOARD_PASSWORD={secrets.token_urlsafe(16)}

# Encryption keys
SECRET_KEY_BASE={b64u(rand_bytes(48))}
REALTIME_DB_ENC_KEY={os.urandom(8).hex()}
VAULT_ENC_KEY={os.urandom(16).hex()}
PG_META_CRYPTO_KEY={b64u(rand_bytes(24))}
LOGFLARE_PUBLIC_ACCESS_TOKEN={b64u(rand_bytes(24))}
LOGFLARE_PRIVATE_ACCESS_TOKEN={b64u(rand_bytes(24))}
S3_PROTOCOL_ACCESS_KEY_ID={os.urandom(16).hex()}
S3_PROTOCOL_ACCESS_KEY_SECRET={os.urandom(32).hex()}

# URLs - use public EIP so local dev tools can reach it too
SUPABASE_PUBLIC_URL=http://18.213.66.136:8050
API_EXTERNAL_URL=http://18.213.66.136:8050/auth/v1

# Database
POSTGRES_HOST=db
POSTGRES_DB=postgres
POSTGRES_PORT=5433

# Supavisor
POOLER_PROXY_PORT_TRANSACTION=6543
POOLER_DEFAULT_POOL_SIZE=20
POOLER_MAX_CLIENT_CONN=100
POOLER_TENANT_ID=tags-agency-leads
POOLER_DB_POOL_SIZE=5

# Studio
STUDIO_DEFAULT_ORGANIZATION=TAGS Agency
STUDIO_DEFAULT_PROJECT=Leads
OPENAI_API_KEY=

# Auth
SITE_URL=http://18.213.66.136:8050
ADDITIONAL_REDIRECT_URLS=
JWT_EXPIRY=3600
DISABLE_SIGNUP=false
MAILER_URLPATHS_CONFIRMATION="/auth/v1/verify"
MAILER_URLPATHS_INVITE="/auth/v1/verify"
MAILER_URLPATHS_RECOVERY="/auth/v1/verify"
MAILER_URLPATHS_EMAIL_CHANGE="/auth/v1/verify"
ENABLE_EMAIL_SIGNUP=true
ENABLE_EMAIL_AUTOCONFIRM=true
SMTP_ADMIN_EMAIL=admin@example.com
SMTP_HOST=supabase-mail
SMTP_PORT=2500
SMTP_USER=fake_mail_user
SMTP_PASS=fake_mail_password
SMTP_SENDER_NAME=fake_sender
ENABLE_ANONYMOUS_USERS=false
ENABLE_PHONE_SIGNUP=true
ENABLE_PHONE_AUTOCONFIRM=true

# Storage
GLOBAL_S3_BUCKET=stub
REGION=stub
MINIO_ROOT_USER=supa-storage
MINIO_ROOT_PASSWORD={secrets.token_urlsafe(12)}secret1234
STORAGE_TENANT_ID=stub

# Functions
FUNCTIONS_VERIFY_JWT=false

# API (PostgREST)
PGRST_DB_SCHEMAS=public,graphql_public
PGRST_DB_MAX_ROWS=1000
PGRST_DB_EXTRA_SEARCH_PATH=public

# Logs
DOCKER_SOCKET_LOCATION=/var/run/docker.sock
GOOGLE_PROJECT_ID=GOOGLE_PROJECT_ID
GOOGLE_PROJECT_NUMBER=GOOGLE_PROJECT_NUMBER

# API gateway (kong)
KONG_HTTP_PORT=8050
KONG_HTTPS_PORT=8443
ANON_KEY_ASYMMETRIC=
SERVICE_ROLE_KEY_ASYMMETRIC=

# imgproxy
IMGPROXY_AUTO_WEBP=true

# TLS proxy (not used)
PROXY_DOMAIN=
CERTBOT_EMAIL=
"""

path = r"C:\Users\TAUSHEF\Downloads\int\_supabase.env"
with open(path, "w", encoding="utf-8") as f:
    f.write(env)
print("WROTE", path)
print("JWT_SECRET:", jwt_secret[:12] + "...")
print("ANON_KEY:", anon[:40] + "...")
print("SERVICE_ROLE_KEY:", service[:40] + "...")
print("POSTGRES_PASSWORD:", postgres_pw[:10] + "...")
