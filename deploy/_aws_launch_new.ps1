$ErrorActionPreference = 'Stop'
$aws = Join-Path $env:LOCALAPPDATA 'Programs\Amazon\AWSCLIV2\aws.exe'

Write-Output '=== 1. Find latest Ubuntu 24.04 AMI ==='
$ami = (& $aws ec2 describe-images --region us-east-1 --profile aws2 --owners 099720109477 --filters "Name=name,Values=ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*" "Name=state,Values=available" --query "sort_by(Images, &CreationDate)[-1].ImageId" --output text 2>&1) | Out-String
$ami = $ami.Trim()
Write-Output "AMI: $ami"
if ($ami -notmatch '^ami-') { Write-Output "FAILED: $ami"; exit 1 }

Write-Output '=== 2. Create/verify key pair ==='
# Import existing ec2-key.pem into this account
$pub = $null
try {
    $pub = (& ssh-keygen -y -f "$PWD\ec2-key.pem" 2>&1) | Out-String
    $pub = $pub.Trim()
} catch { Write-Output 'ssh-keygen failed' }
if ($pub -match '^ssh-') {
    $key = (& $aws ec2 import-key-pair --region us-east-1 --profile aws2 --key-name sba-key --public-key-material $pub --output text 2>&1) | Out-String
    Write-Output "Import: $($key.Trim())"
} else {
    $key = (& $aws ec2 create-key-pair --region us-east-1 --profile aws2 --key-name sba-key --query 'KeyMaterial' --output text 2>&1) | Out-String
    $key = $key.Trim()
    Set-Content -Path "$PWD\ec2-key-new.pem" -Value $key
    Write-Output 'New key saved: ec2-key-new.pem'
}

Write-Output '=== 3. Get default VPC + subnet ==='
$vpc = (& $aws ec2 describe-vpcs --region us-east-1 --profile aws2 --filters "Name=isDefault,Values=true" --query "Vpcs[0].VpcId" --output text 2>&1) | Out-String
$vpc = $vpc.Trim()
$subnet = (& $aws ec2 describe-subnets --region us-east-1 --profile aws2 --filters "Name=vpc-id,Values=$vpc" "Name=default-for-az,Values=true" --query "Subnets[0].SubnetId" --output text 2>&1) | Out-String
$subnet = $subnet.Trim()
Write-Output "VPC: $vpc  SUBNET: $subnet"

Write-Output '=== 4. Create security group (ports 22, 8000, 3001, 5432, 5450) ==='
$sg = (& $aws ec2 create-security-group --region us-east-1 --profile aws2 --group-name sba-db-sg --description "SBA DB instance" --vpc-id $vpc --query 'GroupId' --output text 2>&1) | Out-String
$sg = $sg.Trim()
Write-Output "SG: $sg"
foreach ($port in 22,8000,3001,5450) {
    & $aws ec2 authorize-security-group-ingress --region us-east-1 --profile aws2 --group-id $sg --protocol tcp --port $port --cidr 0.0.0.0/0 2>&1 | Out-Null
}

Write-Output '=== 5. Launch t3.small (2GB, free-tier) 40GB gp3 ==='
$inst = (& $aws ec2 run-instances --region us-east-1 --profile aws2 `
    --image-id $ami --instance-type t3.small --key-name sba-key `
    --security-group-ids $sg --subnet-id $subnet `
    --block-device-mappings "[{\"DeviceName\":\"/dev/sda1\",\"Ebs\":{\"VolumeSize\":40,\"VolumeType\":\"gp3\",\"DeleteOnTermination\":true}}]" `
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=sba-db}]' `
    --query 'Instances[0].InstanceId' --output text 2>&1) | Out-String
$inst = $inst.Trim()
Write-Output "INSTANCE: $inst"

Write-Output '=== 6. Waiting for running + IP ==='
Start-Sleep 8
$ip = (& $aws ec2 describe-instances --region us-east-1 --profile aws2 --instance-ids $inst --query 'Reservations[0].Instances[0].PublicIpAddress' --output text 2>&1) | Out-String
$ip = $ip.Trim()
Write-Output "INSTANCE_ID: $inst"
Write-Output "PUBLIC_IP: $ip"
if ($ip -eq 'None' -or $ip -eq '') { Write-Output 'Allocating EIP...' ; $eip = (& $aws ec2 allocate-address --region us-east-1 --profile aws2 --domain vpc --query 'AllocationId' --output text 2>&1) | Out-String; $eip = $eip.Trim(); & $aws ec2 associate-address --region us-east-1 --profile aws2 --instance-id $inst --allocation-id $eip 2>&1 | Out-Null; Start-Sleep 3; $ip = (& $aws ec2 describe-instances --region us-east-1 --profile aws2 --instance-ids $inst --query 'Reservations[0].Instances[0].PublicIpAddress' --output text 2>&1) | Out-String; $ip = $ip.Trim(); Write-Output "EIP_IP: $ip" }
Write-Output 'LAUNCH_DONE'
