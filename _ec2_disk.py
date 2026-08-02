import subprocess, boto3, time

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=45):
    full = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
            "-i", KEY, HOST, cmd]
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

print("=== DISK USAGE TOP ===")
r = ssh("sudo du -xh --max-depth=1 / 2>/dev/null | sort -rh | head -12; echo ---; sudo journalctl --disk-usage")
print(r.stdout[:2500])

print("\n=== EBS VOLUME ===")
ec2 = boto3.Session(region_name="us-east-1").client("ec2")
vols = ec2.describe_volumes(Filters=[{"Name": "attachment.instance-id", "Values": ["i-09a4dceddec646417"]}])
for v in vols["Volumes"]:
    print("Vol:", v["VolumeId"], "Size:", v["Size"], "State:", v["State"], "Type:", v["VolumeType"])
