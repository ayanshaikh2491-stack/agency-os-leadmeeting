#!/bin/bash
echo "=== docker stats (top by MEM %) ==="
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" 2>/dev/null | sort -t$'\t' -k4 -hr | head -18
echo ""
echo "=== free -h ==="
free -h
echo ""
echo "=== disk ==="
df -h / | tail -1
