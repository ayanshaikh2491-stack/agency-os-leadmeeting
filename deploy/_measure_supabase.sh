#!/bin/bash
echo "=== FREE RAM ==="
free -h
echo ""
echo "=== DOCKER STATS (supabase) ==="
docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}" 2>/dev/null | head -18
echo ""
echo "=== DOCKER TOTAL (supabase+rallly) ==="
docker stats --no-stream --format "{{.MemUsage}}" 2>/dev/null | awk '{print $1}' | paste -sd+ | bc 2>/dev/null || echo "bc missing"
echo ""
echo "=== DISK ==="
df -h / | tail -1
echo ""
echo "=== DOCKER IMAGES SIZE ==="
sudo docker images --format "{{.Repository}}:{{.Tag}} {{.Size}}" 2>/dev/null | head -25
echo ""
echo "=== DOCKER DISK USAGE ==="
sudo docker system df 2>/dev/null
echo ""
echo "=== SUPABASE DIR SIZE ==="
sudo du -sh /home/ubuntu/supabase 2>/dev/null || echo "no /home/ubuntu/supabase"
echo ""
echo "=== RALLLY DIR SIZE ==="
sudo du -sh /home/ubuntu/rallly 2>/dev/null || echo "no rallly"
