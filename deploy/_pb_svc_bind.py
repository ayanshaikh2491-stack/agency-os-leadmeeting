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
    print(r.stdout.strip()[:2500])
    if r.stderr.strip():
        print("ERR:", r.stderr.strip()[:400])
    return r

# 1. Pin PB to localhost in the service file (was 0.0.0.0 - public exposure risk)
ssh("sudo sed -i 's|--http=0.0.0.0:8090|--http=127.0.0.1:8090|' /etc/systemd/system/pocketbase.service && sudo systemctl daemon-reload && echo service-file-updated")
# 2. Kill the orphan PB process so systemd takes ownership
ssh("pkill -f 'pocketbase serve' ; sleep 2 ; pgrep -f 'pocketbase serve' || echo orphan-killed")
# 3. Start + enable via systemd (survives reboot)
ssh("sudo systemctl start pocketbase.service && sudo systemctl enable pocketbase.service && systemctl is-active pocketbase.service")
# 4. Verify health + port
ssh("sleep 2; echo -n 'pb: '; curl -s http://127.0.0.1:8090/api/health; echo; echo -n 'gateway: '; curl -s http://127.0.0.1:8095/health; echo; echo -n 'backend: '; curl -s http://127.0.0.1:8000/api/health; echo")
# 5. Confirm gateway can still reach PB
ssh("sleep 2; curl -s 'http://127.0.0.1:8095/rest/v1/leads?select=id&limit=3' | head -c 300; echo")
