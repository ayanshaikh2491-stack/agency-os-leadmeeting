#!/bin/bash
echo "=== omniroute ==="
ls -la /usr/lib/node_modules/omniroute/ 2>/dev/null | head -5
cat /usr/lib/node_modules/omniroute/package.json 2>/dev/null | head -20

echo ""
echo "=== npm global modules ==="
ls -la /usr/lib/node_modules/ 2>/dev/null

echo ""
echo "=== npm cache ==="
du -sh ~/.npm/ 2>/dev/null
du -sh ~/.cache/npm/ 2>/dev/null

echo ""
echo "=== pip cache ==="
du -sh ~/.cache/pip/ 2>/dev/null

echo ""
echo "=== Docker all containers (incl stopped) ==="
sudo docker ps -a 2>/dev/null

echo ""
echo "=== Docker images ==="
sudo docker images 2>/dev/null

echo ""
echo "=== /snap contents ==="
sudo du -sh /snap/* 2>/dev/null

echo ""
echo "=== Python site-packages size ==="
du -sh /home/ubuntu/.local/lib/python3.12/site-packages/ 2>/dev/null

echo ""
echo "=== /tmp usage ==="
sudo du -sh /tmp/* 2>/dev/null | sort -rh | head -10

echo ""
echo "=== Docker volume list ==="
sudo docker volume ls 2>/dev/null
