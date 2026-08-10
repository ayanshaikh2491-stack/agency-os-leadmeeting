$ErrorActionPreference = 'Continue'
$aws = Join-Path $env:LOCALAPPDATA 'Programs\Amazon\AWSCLIV2\aws.exe'
Write-Output '=== AGENT TOOLKIT SETUP (aws2) ==='
& $aws configure agent-toolkit --yes --region us-east-1 --profile aws2 2>&1
Write-Output 'EXIT=' $LASTEXITCODE
