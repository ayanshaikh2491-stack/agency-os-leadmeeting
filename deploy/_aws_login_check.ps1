$aws = Join-Path $env:LOCALAPPDATA 'Programs\Amazon\AWSCLIV2\aws.exe'
Write-Output '=== TOP-LEVEL HELP (login/agent-toolkit?) ==='
& $aws --help 2>&1 | Select-String -Pattern 'login|agent-toolkit' 
Write-Output '=== CONFIGURE HELP ==='
& $aws configure --help 2>&1 | Select-String -Pattern 'login|agent' -Context 0,1
Write-Output '=== TRY aws login (no args, 5s) ==='
$job = Start-Job { param($p) & $p login 2>&1 } -ArgumentList $aws
if (Wait-Job $job -Timeout 5) { Receive-Job $job | Select-Object -First 20 } else { Write-Output 'TIMED_OUT_INTERACTIVE'; Stop-Job $job }
Remove-Job $job -Force -ErrorAction SilentlyContinue
