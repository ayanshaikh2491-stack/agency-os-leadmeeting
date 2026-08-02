import subprocess, boto3

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"
ENV_LOCAL = r"C:\Users\TAUSHEF\Downloads\int\_supabase.env"

def ssh(cmd, timeout=60):
    full = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=12",
            "-i", KEY, HOST, cmd]
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

# 1. Disk + docker check
r = ssh("df -h / | tail -1 && docker ps --format '{{.Names}} {{.Status}}' && docker system df | head -5")
print("=== DISK + DOCKER ===")
print(r.stdout[:2500])
if r.stderr.strip():
    print("STDERR:", r.stderr[-500:])

# 2. Upload .env
print("\n=== UPLOAD .env ===")
scp = ["scp", "-o", "StrictHostKeyChecking=no", "-i", KEY, ENV_LOCAL, HOST + ":/home/ubuntu/supabase/docker/.env"]
r2 = subprocess.run(scp, capture_output=True, text=True, timeout=90, encoding="utf-8", errors="replace")
print("rc:", r2.returncode, r2.stdout[-500:], r2.stderr[-500:])

# 3. Open port 8050 in security group
print("\n=== SECURITY GROUP 8050 ===")
ec2 = boto3.Session(region_name="us-east-1").client("ec2")
inst = ec2.describe_instances(InstanceIds=["i-09a4dceddec646417"])["Reservations"][0]["Instances"][0]
sg_ids = [g["GroupId"] for g in inst["SecurityGroups"]]
print("SGs:", sg_ids)
for sg in sg_ids:
    try:
        ec2.authorize_security_group_ingress(
            GroupId=sg,
            IpPermissions=[{"IpProtocol": "tcp", "FromPort": 8050, "ToPort": 8050,
                            "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "Supabase Kong HTTP"}]}])
        print("Opened 8050 on", sg)
    except Exception as e:
        print(sg, "->", str(e)[:120])
