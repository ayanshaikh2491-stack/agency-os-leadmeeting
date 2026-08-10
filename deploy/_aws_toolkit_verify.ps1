$ErrorActionPreference = 'Continue'
$aws = Join-Path $env:LOCALAPPDATA 'Programs\Amazon\AWSCLIV2\aws.exe'
Write-Output '=== LIST AVAILABLE SKILLS ==='
& $aws agent-toolkit list-available-skills --region us-east-1 --profile aws2 2>&1 | Select-Object -First 40
Write-Output 'EXIT_SKILLS=' $LASTEXITCODE
