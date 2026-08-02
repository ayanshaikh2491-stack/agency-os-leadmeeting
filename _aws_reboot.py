import boto3

ec2 = boto3.client("ec2", region_name="us-east-1")
iid = "i-09a4dceddec646417"

inst = ec2.describe_instances(InstanceIds=[iid])["Reservations"][0]["Instances"][0]
print("Instance type:", inst.get("InstanceType"))
print("Launch time:", inst.get("LaunchTime"))
print("Root device:", inst.get("RootDeviceName"))
for bd in inst.get("BlockDeviceMappings", []):
    vol = bd["Ebs"]["VolumeId"]
    size = ec2.describe_volumes(VolumeIds=[vol])["Volumes"][0].get("Size")
    print("  Volume:", vol, "size:", size, "GB")

# reboot
print("\nRebooting instance...")
ec2.reboot_instances(InstanceIds=[iid])
print("Reboot requested OK")
