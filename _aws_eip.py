import boto3

ec2 = boto3.client("ec2", region_name="us-east-1")
iid = "i-09a4dceddec646417"

# Elastic IP check
print("=== EIP ===")
try:
    addrs = ec2.describe_addresses()
    for a in addrs.get("Addresses", []):
        print("  EIP:", a.get("PublicIp"), "| instance:", a.get("InstanceId", "-"), "| assoc:", a.get("AssociationId", "-"))
except Exception as e:
    print("  ERROR:", e)

# Recent console output (last 30KB)
print("\n=== CONSOLE OUTPUT (tail) ===")
try:
    out = ec2.get_console_output(InstanceId=iid, Latest=True)
    data = out.get("Output", "") or ""
    print("  Length:", len(data))
    print("  Tail:")
    print(data[-3000:])
except Exception as e:
    print("  ERROR:", e)
