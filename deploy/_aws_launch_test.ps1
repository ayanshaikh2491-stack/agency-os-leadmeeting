$ErrorActionPreference = 'Continue'
$aws = Join-Path $env:LOCALAPPDATA 'Programs\Amazon\AWSCLIV2\aws.exe'
Write-Output '=== AVAILABILITY ZONES ==='
& $aws ec2 describe-availability-zones --region us-east-1 --profile aws2 2>&1 | Select-Object -First 12
Write-Output '=== DRY RUN LAUNCH (t3.micro, free-tier AMI check) ==='
# Find latest Ubuntu 24.04 AMI owned by canonical first
$amis = & $aws ec2 describe-images --region us-east-1 --profile aws2 --owners 099720109477 --filters "Name=name,Values=ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*" "Name=state,Values=available" --query "Images[?Public].ImageId" --max-items 1 2>&1 | Out-String
if ($amis -match 'OptInRequired') { Write-Output 'AMI QUERY: OptInRequired (service still locked)' }
else { Write-Output ("AMI candidates: " + $amis.Trim()) }
Write-Output '=== SUPPORT PLAN CHECK ==='
& $aws support describe-services --profile aws2 --language en 2>&1 | Select-Object -First 5
