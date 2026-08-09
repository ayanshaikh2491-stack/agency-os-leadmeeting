#!/bin/bash
# PocketBase install + superuser on EC2
set -e
PB_VERSION="0.39.10"
PB_DIR="/home/ubuntu/pocketbase"
mkdir -p ${PB_DIR}
cd ${PB_DIR}

echo "=== Download PocketBase ==="
if [ ! -f pocketbase ]; then
  wget -q "https://github.com/pocketbase/pocketbase/releases/download/v${PB_VERSION}/pocketbase_${PB_VERSION}_linux_amd64.zip" -O pb.zip
  echo "downloaded: $(ls -lh pb.zip | awk '{print $5}')"
  # unzip may not exist; use python
  python3 -c "import zipfile; zipfile.ZipFile('pb.zip').extractall('.')" && rm -f pb.zip
fi
ls -lh pocketbase
chmod +x pocketbase

echo "=== Start PocketBase (port 8090) ==="
pkill -f 'pocketbase serve' 2>/dev/null || true
sleep 1
nohup ${PB_DIR}/pocketbase serve --http 127.0.0.1:8090 --dir ${PB_DIR}/pb_data > ${PB_DIR}/pb_serve.log 2>&1 &
sleep 3
curl -sf http://127.0.0.1:8090/api/health || echo "PB NOT UP"

echo "=== Superuser upsert ==="
${PB_DIR}/pocketbase superuser upsert admin@tagsagency.local pb-admin-2026-x9 2>&1 | tail -2

echo "=== Health after ==="
curl -sf http://127.0.0.1:8090/api/health
echo ""
echo "=== Collections ==="
curl -sf -X POST http://127.0.0.1:8090/api/collections/_superusers/auth-with-password \
  -H 'Content-Type: application/json' \
  -d '{"identity":"admin@tagsagency.local","password":"pb-admin-2026-x9"}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('TOKEN_OK' if d.get('token') else d)" 2>/dev/null || echo "auth check failed"
