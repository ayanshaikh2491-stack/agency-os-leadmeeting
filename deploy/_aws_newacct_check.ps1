$ErrorActionPreference = 'Continue'
$aws = Join-Path $env:LOCALAPPDATA 'Programs\Amazon\AWSCLIV2\aws.exe'
Write-Output '=== FREE-TIER ELIGIBLE TYPES (aws2) ==='
$r = & $aws ec2 describe-instance-types --region us-east-1 --profile aws2 --filters "Name=free-tier-eligible,Values=true" --query "InstanceTypes[*].[InstanceType,VCpuInfo.DefaultVCpus,MemoryInfo.SizeInMiB]" --output text 2>&1
$r | ForEach-Object { $_ }
Write-Output '=== EXISTING INSTANCES (aws2) ==='
& $aws ec2 describe-instances --region us-east-1 --profile aws2 --query "Reservations[*].Instances[*].[InstanceId,InstanceType,State.Name,PublicIpAddress]" --output text 2>&1
Write-Output '=== EXISTING KEY PAIRS (aws2) ==='
& $aws ec2 describe-key-pairs --region us-east-1 --profile aws2 --query "KeyPairs[*].KeyName" --output text 2>&1
Write-Output '=== EXISTING VPC/SG ==='
& $aws ec2 describe-security-groups --region us-east-1 --profile aws2 --query "SecurityGroups[*].[GroupId,GroupName]" --output text 2>&1
