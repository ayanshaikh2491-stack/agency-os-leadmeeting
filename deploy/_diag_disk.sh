#!/bin/bash
echo '===DISK_TOP==='
sudo du -x -h --max-depth=1 / 2>/dev/null | sort -h -r | head -12
echo '===DOCKER_DISK==='
sudo docker system df 2>/dev/null
echo '===DOCKER_IMAGES==='
sudo docker images --format '{{.Repository}}:{{.Tag}} {{.Size}}' 2>/dev/null | head -20
echo '===DOCKER_PS_ALL==='
sudo docker ps -a --format '{{.Names}} {{.Status}}' 2>/dev/null | head -20
echo '===BACKEND_DIR==='
sudo du -sh /home/ubuntu/sba-backend 2>/dev/null
echo '===VAR_LOG==='
sudo du -sh /var/log 2>/dev/null
echo '===JOURNAL==='
sudo journalctl --disk-usage 2>/dev/null
