import subprocess, json

key = 'ec2-key.pem'
host = 'ubuntu@18.213.66.136'

# Step 1: Create docker-compose.yml for Rallly
# We need to generate SECRET_PASSWORD first
r = subprocess.run(['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', host,
    'openssl rand -hex 32'],
    capture_output=True, text=True, timeout=10)
secret = r.stdout.strip()

# Create the compose file
docker_compose = f'''services:
  rallly_db:
    image: postgres:16-alpine
    restart: always
    ports:
      - "5450:5432"
    volumes:
      - db-data:/var/lib/postgresql/data
    environment:
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=rallly
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  rallly:
    image: lukevella/rallly:latest
    restart: always
    depends_on:
      rallly_db:
        condition: service_healthy
    ports:
      - "3001:3000"
    environment:
      - DATABASE_URL=postgres://postgres:postgres@rallly_db/rallly
      - NEXT_PUBLIC_BASE_URL=http://18.213.66.136:3001
      - SECRET_PASSWORD={secret}
      - SUPPORT_EMAIL=sba@agency-os.com
volumes:
  db-data:
    driver: local
'''

# Write compose file to EC2
subprocess.run(['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', host,
    'mkdir -p /home/ubuntu/rallly'],
    capture_output=True, timeout=10)

subprocess.run(['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', host,
    'cat > /home/ubuntu/rallly/docker-compose.yml'],
    input=docker_compose, text=True, capture_output=True, timeout=10)

print("docker-compose.yml created")

# Step 2: Pull images
print("\n=== Pulling images ===")
r = subprocess.run(['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', host,
    'cd /home/ubuntu/rallly && sudo docker compose pull 2>&1 | tail -10'],
    capture_output=True, text=True, timeout=300)
print(r.stdout[-500:])
if r.stderr.strip(): print(r.stderr[-200:])

# Step 3: Start containers
print("\n=== Starting Rallly ===")
r = subprocess.run(['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', host,
    'cd /home/ubuntu/rallly && sudo docker compose up -d 2>&1'],
    capture_output=True, text=True, timeout=60)
print(r.stdout[-500:])
if r.stderr.strip(): print(r.stderr[-200:])

# Step 4: Check status
print("\n=== Status ===")
r = subprocess.run(['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', host,
    'sleep 8 && sudo docker compose -f /home/ubuntu/rallly/docker-compose.yml ps'],
    capture_output=True, text=True, timeout=30)
print(r.stdout)

# Step 5: Test
print("\n=== Testing ===")
r = subprocess.run(['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', host,
    'curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:3001/'],
    capture_output=True, text=True, timeout=15)
print(f"HTTP: {r.stdout}")
