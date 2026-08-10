$ErrorActionPreference = 'Stop'
$aws = Join-Path $env:LOCALAPPDATA 'Programs\Amazon\AWSCLIV2\aws.exe'
$awsDir = Join-Path $env:USERPROFILE '.aws'
$cred = Join-Path $awsDir 'credentials'
$cfg = Join-Path $awsDir 'config'

Write-Output '=== BACKUP ==='
if (Test-Path $cred) { Copy-Item $cred "$cred.bak" -Force; Write-Output 'credentials.bak saved' } else { Write-Output 'no credentials file' }
if (Test-Path $cfg) { Copy-Item $cfg "$cfg.bak" -Force; Write-Output 'config.bak saved' } else { Write-Output 'no config file' }

Write-Output '=== CURRENT DEFAULT IDENTITY ==='
try { & $aws sts get-caller-identity 2>&1 } catch { Write-Output 'no current identity' }

Write-Output '=== SET REGION us-east-1 ==='
& $aws configure set region us-east-1

Write-Output '=== LOGIN (browser will open; running with 5s head start) ==='
Write-Output 'INTERACTIVE_LOGIN_START'
