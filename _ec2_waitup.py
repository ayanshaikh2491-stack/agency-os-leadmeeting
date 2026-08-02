import subprocess, time, json, sys

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=45):
    full = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
            "-i", KEY, HOST, cmd]
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

deadline = time.time() + 900  # 15 min
while time.time() < deadline:
    r = ssh("docker ps --format '{{.Names}} {{.Status}}' | wc -l; tail -2 /tmp/supabase_up.log | head -2")
    n = (r.stdout or "").strip().split("\n")[0]
    tail = (r.stdout or "").split("\n")[-1][:80] if (r.stdout or "").strip() else ""
    sup = 0
    if r.stdout:
        sup = sum(1 for line in r.stdout.split("\n") if "supabase-" in line)
    print(f"JCODE_PROGRESS {json.dumps({'current': sup, 'total': 12, 'unit': 'supabase containers', 'message': f'containers up: {sup}, last: {tail}'})}", flush=True)
    if sup >= 11:
        break
    time.sleep(45)

r = ssh("docker ps --format '{{.Names}} {{.Status}}' | sort")
print("=== FINAL ===")
print(r.stdout[:3000])
if r.stderr.strip():
    print("ERR:", r.stderr[-500:])
