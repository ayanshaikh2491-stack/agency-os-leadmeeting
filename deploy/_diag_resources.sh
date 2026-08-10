#!/bin/bash
echo '===MEM==='
free -h
echo '===DISK==='
df -h / | tail -1
echo '===DOCKER_RAM==='
docker stats --no-stream --format '{{.Name}}\t{{.MemUsage}}' 2>/dev/null | sort -k2 -h -r | head -14
echo '===TOP_PROC==='
ps aux --sort=-%mem | head -6
echo '===SWAP==='
swapon --show 2>/dev/null || cat /proc/swaps
