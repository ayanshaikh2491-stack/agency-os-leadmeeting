import boto3
import sys

try:
    import boto3
    print("boto3 version:", boto3.__version__)
except ImportError as e:
    print("boto3 NOT installed:", e)
    sys.exit(1)

ec2 = boto3.client("ec2", region_name="us-east-1")
try:
    resp = ec2.describe_instances()
except Exception as e:
    print("ERROR describing instances:", e)
    sys.exit(1)

for r in resp.get("Reservations", []):
    for inst in r.get("Instances", []):
        iid = inst["InstanceId"]
        state = inst["State"]["Name"]
        ip = inst.get("PublicIpAddress") or inst.get("PrivateIpAddress") or "-"
        key = inst.get("KeyName", "-")
        tags = {t["Key"]: t["Value"] for t in inst.get("Tags", [])}
        print(f"  {iid} | {state} | {ip} | key={key} | tags={tags}")
