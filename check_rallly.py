import subprocess
key = 'ec2-key.pem'
host = 'ubuntu@18.213.66.136'

# Wait and check health
r = subprocess.run(['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', host,
    'sleep 15 && sudo docker compose -f /home/ubuntu/rallly/docker-compose.yml ps && echo === && curl -s -o /dev/null -w "%{http_code}" --max-time 10 http://localhost:3001/ && echo === && sudo docker compose -f /home/ubuntu/rallly/docker-compose.yml logs --tail=20 rallly'],
    capture_output=True, text=True, timeout=60)
print(r.stdout[-2000:])
if r.stderr.strip(): print(r.stderr[-300:])
