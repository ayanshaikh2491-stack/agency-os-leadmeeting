$aws = Join-Path $env:LOCALAPPDATA 'Programs\Amazon\AWSCLIV2\aws.exe'
Write-Output '=== VERSION ==='
& $aws --version
Write-Output '=== PROFILES ==='
& $aws configure list-profiles
Write-Output '=== LOGIN HELP ==='
& $aws login --help 2>&1 | Select-Object -First 25
