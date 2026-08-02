import boto3

ec2 = boto3.client("ec2", region_name="us-east-1")
iid = "i-09a4dceddec646417"

# Status checks
print("=== STATUS CHECKS ===")
try:
    st = ec2.describe_instance_status(InstanceIds=[iid])
    for s in st.get("InstanceStatuses", []):
        print("  State:", s.get("InstanceState", {}).get("Name"))
        print("  System status:", s.get("SystemStatus", {}).get("Status"))
        print("  Instance status:", s.get("InstanceStatus", {}).get("Status"))
        for d in s.get("StatusDetails", []):
            print("   ", d.get("Name"), "->", d.get("Status"), "|", d.get("ImpairedSince", "n/a"))
except Exception as e:
    print("  ERROR:", e)

# Security groups
print("\n=== SECURITY GROUPS ===")
try:
    inst = ec2.describe_instances(InstanceIds=[iid])["Reservations"][0]["Instances"][0]
    for sg in inst.get("SecurityGroups", []):
        print("  SG:", sg["GroupId"], sg["GroupName"])
        try:
            desc = ec2.describe_security_groups(GroupIds=[sg["GroupId"]])["SecurityGroups"][0]
            for perm in desc.get("IpPermissions", []):
                proto = perm.get("IpProtocol", "-")
                ports = f"{perm.get('FromPort','-')}-{perm.get('ToPort','-')}"
                for rng in perm.get("IpRanges", []):
                    print(f"    INGRESS {proto} {ports} from {rng['CidrIp']}")
                for rng in perm.get("Ipv6Ranges", []):
                    print(f"    INGRESS {proto} {ports} from {rng['CidrIpv6']}")
        except Exception as e:
            print("    ERROR:", e)
except Exception as e:
    print("  ERROR:", e)

# EIP / NIC
print("\n=== NETWORK ===")
try:
    inst = ec2.describe_instances(InstanceIds=[iid])["Reservations"][0]["Instances"][0]
    print("  Private IP:", inst.get("PrivateIpAddress"))
    print("  Public IP:", inst.get("PublicIpAddress"))
    print("  VPC:", inst.get("VpcId"), "Subnet:", inst.get("SubnetId"))
    for eni in inst.get("NetworkInterfaces", []):
        print("  ENI:", eni["NetworkInterfaceId"], "status:", eni.get("Status"), "sg:", [g["GroupId"] for g in eni.get("Groups", [])])
except Exception as e:
    print("  ERROR:", e)

# SSM ping
print("\n=== SSM AGENT ===")
try:
    ssm = boto3.client("ssm", region_name="us-east-1")
    info = ssm.describe_instance_information(Filters=[{"Key": "InstanceIds", "Values": [iid]}])
    for ii in info.get("InstanceInformationList", []):
        print("  SSM connected:", ii.get("PingStatus"), "| agent:", ii.get("AgentVersion"), "| platform:", ii.get("PlatformName"), ii.get("PlatformVersion"))
    if not info.get("InstanceInformationList"):
        print("  SSM agent NOT registered (no Session Manager access)")
except Exception as e:
    print("  ERROR:", e)
