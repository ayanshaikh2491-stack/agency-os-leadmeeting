import subprocess, os

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=120):
    print(">>>", cmd)
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                        "-o", "ConnectTimeout=10", "-i", KEY, HOST, cmd],
                       capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    print("rc=", r.returncode)
    print(r.stdout.strip()[:3000])
    if r.stderr.strip():
        print("ERR:", r.stderr.strip()[:400])
    return r

print("=== supabase image sizes BEFORE ===")
ssh("docker images --format '{{.Repository}}:{{.Tag}} {{.Size}}' | grep -i supabase")
print("=== compose down (keep volumes for rollback) ===")
ssh("cd /home/ubuntu/supabase/docker && docker compose down 2>&1 | tail -5")
print("=== remove supabase images ===")
ssh("docker images --format '{{.Repository}}:{{.Tag}}' | grep -i supabase | xargs -r docker rmi 2>&1 | tail -8")
print("=== disk AFTER ===")
ssh("df -h /")
print("=== docker system df AFTER ===")
ssh("docker system df")
print("=== RAM now ===")
ssh("free -h")
