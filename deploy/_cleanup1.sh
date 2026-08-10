#!/bin/bash
echo '===BEFORE==='
free -h | head -2
df -h / | tail -1
echo '===KILL ORPHANED BACKFILL CHROME (port 9252, .sba-backfill-profile)==='
pgrep -af 'sba-backfill-profile' && pkill -f 'sba-backfill-profile' && echo KILLED || echo NONE_RUNNING
sleep 1
pgrep -af 'sba-backfill-profile' || echo CONFIRMED_DEAD
echo '===VACUUM JOURNAL TO 200M==='
sudo journalctl --vacuum-size=200M
echo '===AFTER==='
free -h | head -2
df -h / | tail -1
