import subprocess, os

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=30):
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                        "-o", "ConnectTimeout=8", "-i", KEY, HOST, cmd],
                       capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    print("rc=", r.returncode)
    print(r.stdout.strip()[:4000])
    if r.stderr.strip():
        print("ERR:", r.stderr.strip()[:400])
    return r

print("=== autopilot: where leads are loaded for judging (grep load_leads / find_leads / candidates) ===")
ssh("grep -n 'load_leads\\|find_candidate\\|judge\\|candidate\\|def run_once\\|def _run_once' /home/ubuntu/sba-backend/admin/agency/sba_autopilot.py | head -30", timeout=30)
