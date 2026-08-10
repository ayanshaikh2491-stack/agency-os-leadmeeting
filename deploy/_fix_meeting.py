"""Deploy the 3 stale files (sba_meeting, sba_biztypes, sba.py) + restart autopilot."""
import os, subprocess, sys, time, shutil
sys.path.insert(0, os.getcwd())

KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=60):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
         "-o", "ConnectTimeout=10", "-i", KEY, HOST, cmd],
        capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

files = [
    ("admin/tools/sba_meeting.py", "/home/ubuntu/sba-backend/admin/tools/sba_meeting.py"),
    ("admin/agency/sba_biztypes.py", "/home/ubuntu/sba-backend/admin/agency/sba_biztypes.py"),
    ("admin/workspace/agents/sba.py", "/home/ubuntu/sba-backend/admin/workspace/agents/sba.py"),
]

for src, dst in files:
    r = subprocess.run(
        ["scp", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
         "-o", "ConnectTimeout=10", "-i", KEY, src, f"{HOST}:{dst}"],
        capture_output=True, text=True, timeout=90, encoding="utf-8", errors="replace")
    print(f"scp {src}: rc={r.returncode}")

# syntax check all on EC2
r = ssh("cd /home/ubuntu/sba-backend && python -m py_compile admin/tools/sba_meeting.py admin/agency/sba_biztypes.py admin/workspace/agents/sba.py admin/agency/sba_autopilot.py && echo SYNTAX_OK")
print("syntax:", r.stdout.strip(), r.stderr[-200:] if r.returncode else "")

# import check (the exact thing that was crashing)
r = ssh("cd /home/ubuntu/sba-backend && venv/bin/python -c 'import admin.tools.sba_email_client as m; from admin.tools.sba_meeting import SBAMeetingManager; from admin.agency.sba_biztypes import get_workspace_config; from admin.workspace.agents.sba import sba_run_tools; print(\"IMPORT_ALL_OK\")'")
print("import:", r.stdout.strip(), r.stderr[-300:] if r.returncode else "")

# restart
r = ssh("sudo -n systemctl restart sba-autopilot && echo RESTARTED")
print("restart:", r.stdout.strip(), r.stderr[-200:] if r.returncode else "")
