$aws = Join-Path $env:LOCALAPPDATA 'Programs\Amazon\AWSCLIV2\aws.exe'
Write-Output '=== PROFILES ==='
& $aws configure list-profiles
Write-Output '=== IDENTITY aws2 ==='
& $aws sts get-caller-identity --profile aws2
Write-Output '=== IDENTITY default (should be old account) ==='
& $aws sts get-caller-identity --profile default
