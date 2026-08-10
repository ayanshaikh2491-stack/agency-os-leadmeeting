"""List free-tier-eligible instance types in us-east-1."""
import boto3

ec2 = boto3.client("ec2", region_name="us-east-1")
resp = ec2.describe_instance_types(
    Filters=[{"Name": "free-tier-eligible", "Values": ["true"]}],
)
rows = []
for t in resp.get("InstanceTypes", []):
    vcpu = t.get("VCpuInfo", {}).get("DefaultVCpus", "?")
    mem = t.get("MemoryInfo", {}).get("SizeInMiB", 0)
    rows.append((t["InstanceType"], vcpu, mem / 1024))
rows.sort()
print(f"{'TYPE':<20} {'vCPU':<6} {'RAM_GB':<8}")
for r in rows:
    print(f"{r[0]:<20} {r[1]:<6} {r[2]:<8.1f}")
