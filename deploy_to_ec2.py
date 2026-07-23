import subprocess, os

key = 'C:/Users/TAUSHEF/Downloads/int/ec2-key.pem'
ssh_base = ['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', '-o', 'UserKnownHostsFile=/dev/null', 'ubuntu@18.213.66.136']
scp_base = ['scp', '-i', key, '-o', 'StrictHostKeyChecking=no', '-o', 'UserKnownHostsFile=/dev/null']

def run(cmd_list):
    r = subprocess.run(cmd_list, capture_output=True, text=True, timeout=30)
    return r.stdout, r.stderr, r.returncode

# 1. Create directory structure on EC2
print('=== Creating directories ===')
cmd = ssh_base + ['mkdir -p /home/ubuntu/sba-backend/admin/agency /home/ubuntu/sba-backend/admin/api/routes /home/ubuntu/sba-backend/admin/config /home/ubuntu/sba-backend/admin/tools /home/ubuntu/sba-backend/admin/api/models /home/ubuntu/sba-backend/admin/workspace']
out, err, rc = run(cmd)
print(out, err[:100] if err else '')

# 2. Copy all backend files
print('=== Copying files ===')
local_root = 'C:/Users/TAUSHEF/Downloads/int/admin'
remote_root = 'ubuntu@18.213.66.136:/home/ubuntu/sba-backend/admin'

files_to_copy = [
    ('main.py', '.'),
    ('requirements.txt', '.'),
    ('__init__.py', '.'),
    ('agency/__init__.py', 'agency'),
    ('agency/sba.py', 'agency'),
    ('agency/sba_skills.py', 'agency'),
    ('agency/sba_store.py', 'agency'),
    ('agency/ceo.py', 'agency'),
    ('config/__init__.py', 'config'),
    ('config/settings.py', 'config'),
    ('api/__init__.py', 'api'),
    ('api/models/__init__.py', 'api/models'),
    ('api/models/schemas.py', 'api/models'),
    ('api/routes/__init__.py', 'api/routes'),
    ('api/routes/sba.py', 'api/routes'),
    ('tools/__init__.py', 'tools'),
    ('tools/chrome_tool.py', 'tools'),
    ('workspace/__init__.py', 'workspace'),
    ('workspace/manager.py', 'workspace'),
    ('agency/agency_agents.py', 'agency'),
    ('agency/swarm.py', 'agency'),
    ('api/routes/ceo.py', 'api/routes'),
    ('api/routes/swarm.py', 'api/routes'),
    ('api/routes/workspace.py', 'api/routes'),
]

for local_file, remote_dir in files_to_copy:
    local_path = os.path.join(local_root, local_file)
    if os.path.exists(local_path):
        cmd = scp_base + [local_path, remote_root + '/' + remote_dir + '/']
        out, err, rc = run(cmd)
        if rc != 0:
            print(f'FAIL {local_file}: {err[:100]}')
        else:
            print(f'OK   {local_file}')
    else:
        print(f'MISS {local_file}')
