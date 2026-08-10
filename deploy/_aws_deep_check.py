"""Deep check of old AWS account - what exactly does it have."""
import boto3
from datetime import datetime, timezone

print("=== PROFILE ===")
session = boto3.Session()
print("region:", session.region_name)

print("\n=== EC2 INSTANCES (all) ===")
ec2 = session.client("ec2", region_name="us-east-1")
resp = ec2.describe_instances()
for r in resp["Reservations"]:
    for i in r["Instances"]:
        print(f"ID: {i['InstanceId']}")
        print(f"  Type: {i['InstanceType']}")
        print(f"  State: {i['State']['Name']}")
        print(f"  LaunchTime: {i['LaunchTime'].isoformat()}")
        print(f"  vCPUs/Mem: {i.get('CpuOptions', {}).get('CoreCount')} cores")
        print(f"  AZ: {i.get('Placement', {}).get('AvailabilityZone')}")
        tags = {t['Key']: t['Value'] for t in i.get('Tags', [])}
        print(f"  Tags: {tags}")
        print(f"  PublicIP: {i.get('PublicIpAddress')}")
        for b in i.get("BlockDeviceMappings", []):
            vol = b.get("Ebs", {}).get("VolumeId", "?")
            try:
                vs = ec2.describe_volumes(VolumeIds=[vol])["Volumes"][0]
                print(f"  EBS: {vol} {vs['Size']}GB {vs['VolumeType']}")
            except Exception:
                print(f"  EBS: {vol} ?")

print("\n=== VOLUMES ===")
vols = ec2.describe_volumes()
for v in vols["Volumes"]:
    print(f"{v['VolumeId']} {v['Size']}GB {v['State']} type={v['VolumeType']} iops={v.get('Iops')}")

print("\n=== FREE TIER USAGE (last 3 months) ===")
try:
    ft = session.client("freetier", region_name="us-east-1")
    free = ft.get_free_tier_usage(
        filter={"dimensions": ["USAGE_TYPE"], "matchOptions": ["CONTAINS"], "values": ["BoxUsage"]}
    )
    for d in free.get("freeTierUsages", [])[:10]:
        print(d)
except Exception as e:
    print("freetier API:", type(e).__name__, str(e)[:300])

print("\n=== ACCOUNT ALIAS / INFO ===")
try:
    iam = session.client("iam")
    aliases = iam.list_account_aliases().get("AccountAliases", [])
    print("aliases:", aliases)
    acct = iam.get_user()
    print("user:", acct.get("User", {}).get("UserName"))
except Exception as e:
    print("iam:", type(e).__name__, str(e)[:200])

print("\n=== EC2 INSTANCE TYPES CHECK (t3.micro vs t3.small free-tier?) ===")
try:
    # Check instance-type offerings to see if t3.small is free-tier eligible
    off = ec2.describe_instance_type_offerings(
        LocationType="region",
        Filters=[{"Name": "instance-type", "Values": ["t3.micro", "t3.small", "t3.medium"]}],
    )
    types = sorted({o["InstanceType"] for o in off["InstanceTypeOfferings"]})
    print("available in us-east-1:", types)
except Exception as e:
    print("offerings:", type(e).__name__, str(e)[:200])
