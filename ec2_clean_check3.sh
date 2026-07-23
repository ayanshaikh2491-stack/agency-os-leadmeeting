#!/bin/bash
echo "=== omniroute package.json ==="
cat /usr/lib/node_modules/omniroute/package.json 2>/dev/null

echo ""
echo "=== omniroute what is it ==="
ls -la /usr/lib/node_modules/omniroute/@omniroute/ 2>/dev/null

echo ""
echo "=== Is any process using omniroute? ==="
ps aux | grep -i omniroute 2>/dev/null

echo ""
echo "=== mcporter ==="
cat /usr/lib/node_modules/mcporter/package.json 2>/dev/null | head -15

echo ""
echo "=== Largest python packages ==="
du -sh /home/ubuntu/.local/lib/python3.12/site-packages/*/ 2>/dev/null | sort -rh | head -20

echo ""
echo "=== pip cache ==="
du -sh /home/ubuntu/.cache/pip/ 2>/dev/null
sudo du -sh /root/.cache/pip/ 2>/dev/null

echo ""
echo "=== Journal log age ==="
sudo journalctl --list-boots 2>/dev/null

echo ""
echo "=== apt autoremovable ==="
sudo apt-get --just-print autoremove 2>/dev/null | grep "Remv"
