$aws = Join-Path $env:LOCALAPPDATA 'Programs\Amazon\AWSCLIV2\aws.exe'
Write-Output '=== AVAILABLE COMMANDS (top-level) ==='
$help = & $aws help 2>&1 | Out-String
($help -split "`n") | Select-String -Pattern '^\s+(login|configure|sts|ec2|agent-toolkit)\s' | Select-Object -First 20
Write-Output '=== full help around login ==='
($help -split "`n") | Select-String -Pattern 'login' | Select-Object -First 10
Write-Output '=== CONFIGURE SUBCOMMANDS ==='
$che = & $aws configure help 2>&1 | Out-String
($che -split "`n") | Select-String -Pattern 'agent-toolkit|login' | Select-Object -First 10
