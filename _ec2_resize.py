import subprocess, boto3, time, sys

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"
VOL = "vol-02a672578a70dbbde"

def ssh(cmd, timeout=120):
    full = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
            "-i", KEY, HOST, cmd]
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

ec2 = boto3.Session(region_name="us-east-1").client("ec2")

# 1. Resize volume 20 -> 40 GB
print("=== RESIZE EBS 20->40 ===")
try:
    ec2.modify_volume(VolumeId=VOL, Size=40)
    print("modify_volume sent")
except Exception as e:
    print("modify err:", str(e)[:200])

# Wait for modification state 'optimizing' or 'completed'
for i in range(30):
    st = ec2.describe_volumes_modifications(VolumeIds=[VOL])["VolumesModifications"][0]
    if st["ModificationState"] in ("optimizing", "completed"):
        print(f"mod state: {st['ModificationState']} (progress {st.get('Progress')}%)")
        if st["ModificationState"] == "completed":
            break
    time.sleep(10)
    print("waiting...", i)

# 2. Cleanup: journals + partial docker images
print("\n=== CLEANUP ===")
r = ssh("sudo journalctl --vacuum-size=200M 2>&1 | tail -2; docker system prune -af --volumes=false 2>&1 | tail -3; df -h / | tail -1")
print(r.stdout[:1500])
if r.stderr.strip():
    print("ERR:", r.stderr[-300:])

# 3. Extend filesystem
print("\n=== EXTEND FS ===")
r = ssh("lsblk | head -10")
print(r.stdout[:800])
