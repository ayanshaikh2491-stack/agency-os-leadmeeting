$ErrorActionPreference = 'Continue'
$aws = Join-Path $env:LOCALAPPDATA 'Programs\Amazon\AWSCLIV2\aws.exe'
Write-Output '=== BILLING ACCOUNT BALANCE (new API) ==='
& $aws billing get-account-balance --region us-east-1 --profile aws2 2>&1 | Select-Object -First 20
Write-Output '=== COST EXPLORER (may need opt-in) ==='
& $aws ce get-cost-and-usage --region us-east-1 --profile aws2 --time-period Start=2026-08-01,End=2026-08-08 --granularity MONTHLY --metrics UnblendedCost 2>&1 | Select-Object -First 20
Write-Output '=== CREDIT MANAGEMENT (free tier credits?) ==='
& $aws billing list-billing-views --region us-east-1 --profile aws2 2>&1 | Select-Object -First 15
