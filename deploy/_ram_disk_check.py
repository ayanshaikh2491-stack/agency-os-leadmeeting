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

print("=== RAM now ===")
ssh("free -h")
print("=== Disk now ===")
ssh("df -h /")
print("=== Docker disk usage (images/containers/volumes) ===")
ssh("docker system df")
print("=== Supabase compose disk footprint ===")
ssh("du -sh /home/ubuntu/supabase/docker/volumes/db/data 2>/dev/null; docker images | grep -c supabase; docker ps -a --format '{{.Names}}' | grep -c supabase")
print("=== swap pressure now ===")
ssh("cat /proc/meminfo | grep -E 'SwapTotal|SwapFree|SwapCached'")
