import subprocess, tempfile, os

key = 'ec2-key.pem'
host = 'ubuntu@18.213.66.136'

# Create a comprehensive setup script for EC2
setup_script = '''#!/bin/bash
set -e
echo "=== Installing Docker ==="
sudo apt-get update -qq
sudo apt-get install -y -qq ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update -qq
sudo apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker ubuntu
echo "Docker installed OK"

echo "=== Creating Rallly directory ==="
mkdir -p /home/ubuntu/rallly

echo "=== Creating docker-compose.yml ==="
SECRET=$(openssl rand -hex 32)
cat > /home/ubuntu/rallly/docker-compose.yml << 'COMPOSE_EOF'
services:
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
      - SECRET_PASSWORD=__SECRET__
      - SUPPORT_EMAIL=sba@agency-os.com
volumes:
  db-data:
    driver: local
COMPOSE_EOF

# Replace placeholder with generated secret
sed -i "s/__SECRET__/$SECRET/" /home/ubuntu/rallly/docker-compose.yml
echo "docker-compose.yml created with secret length: ${#SECRET}"

echo "=== Creating nginx config for rallly ==="
sudo tee /etc/nginx/sites-available/rallly << 'NGINX_EOF'
server {
    listen 80;
    server_name 18.213.66.136;

    location /rallly/ {
        proxy_pass http://127.0.0.1:3001/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
NGINX_EOF

# Actually let's keep it simple - use subdomain approach later
# For now just port 3001 is fine

echo "=== Docker compose pull ==="
cd /home/ubuntu/rallly
sudo docker compose pull 2>&1 | tail -5

echo "=== Docker compose up ==="
sudo docker compose up -d 2>&1 | tail -5

echo "=== Status ==="
sleep 5
sudo docker compose ps
'''

# Write script to file, then scp and execute
local_path = os.path.join(tempfile.gettempdir(), 'setup_rallly.sh')
with open(local_path, 'w') as f:
    f.write(setup_script)

# SCP the script to EC2
subprocess.run(
    ['scp', '-i', key, '-o', 'StrictHostKeyChecking=no',
     '-o', 'ConnectTimeout=10', local_path, f'{host}:/tmp/setup_rallly.sh'],
    capture_output=True, timeout=30)

# Execute it
print("Installing Docker + setting up Rallly (this takes 2-3 min)...")
r = subprocess.run(
    ['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', host,
     'bash /tmp/setup_rallly.sh'],
    capture_output=True, text=True, timeout=300)

print("STDOUT:", r.stdout[-1500:])
if r.stderr.strip(): print("STDERR:", r.stderr[-500:])

# Verify
print("\n=== Verifying ===")
r = subprocess.run(
    ['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', host,
     'sudo docker compose -f /home/ubuntu/rallly/docker-compose.yml ps'],
    capture_output=True, text=True, timeout=15)
print(r.stdout)

# Test endpoint
print("\n=== Testing Rallly via curl ===")
r = subprocess.run(
    ['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', host,
     'curl -s -o /dev/null -w "%{http_code}" http://localhost:3001/'],
    capture_output=True, text=True, timeout=10)
print(f"HTTP status: {r.stdout}")
