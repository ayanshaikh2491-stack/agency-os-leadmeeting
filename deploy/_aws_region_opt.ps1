$ErrorActionPreference = 'Continue'
$aws = Join-Path $env:LOCALAPPDATA 'Programs\Amazon\AWSCLIV2\aws.exe'
Write-Output '=== REGION OPT STATUS (account API) ==='
& $aws account get-region-opt-status --region-name us-east-1 --profile aws2 2>&1
Write-Output '=== ACCOUNT IDENTITY ==='
& $aws sts get-caller-identity --profile aws2 2>&1
Write-Output '=== EC2 DESCRIBE-REGIONS us-east-1 ==='
& $aws ec2 describe-regions --region us-east-1 --profile aws2 2>&1 | Select-Object -First 15
Write-Output '=== ORGANIZATIONS (member or standalone?) ==='
& $aws organizations describe-organization --profile aws2 2>&1 | Select-Object -First 15
