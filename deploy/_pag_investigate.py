import subprocess, os

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=60):
    print(">>>", cmd)
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                        "-o", "ConnectTimeout=10", "-i", KEY, HOST, cmd],
                       capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    print("rc=", r.returncode)
    print(r.stdout.strip()[:3500])
    if r.stderr.strip():
        print("ERR:", r.stderr.strip()[:400])
    return r

print("=== autopilot lead fetch (list/select/page) ===")
ssh("grep -n 'rest/v1/leads\\|list_records\\|page=\\|select=.*order\\|created_at.asc\\|per_page\\|limit=' /home/ubuntu/sba-backend/admin/agency/sba_autopilot.py | head -30", timeout=45)
print("=== supabase client list implementation ===")
ssh("grep -rn 'def list\\|def fetch\\|page=\\|range\\|limit\\|count=exact' /home/ubuntu/sba-backend/admin/supabase_client.py 2>/dev/null | head -30; ls /home/ubuntu/sba-backend/admin/ | grep -i supabase", timeout=45)
