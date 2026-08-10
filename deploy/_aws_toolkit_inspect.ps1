$ErrorActionPreference = 'Continue'
$env:PYTHONIOENCODING = 'utf-8'
$aws = Join-Path $env:LOCALAPPDATA 'Programs\Amazon\AWSCLIV2\aws.exe'
Write-Output '=== SKILL NAMES ==='
& $aws agent-toolkit list-available-skills --region us-east-1 --profile aws2 2>$null | Out-String -Stream | Select-String -Pattern '"name":' | ForEach-Object { $_.Line.Trim() }
Write-Output '=== JCODE SKILLS DIR (aws-installed?) ==='
$jskills = Join-Path $env:USERPROFILE '.jcode\skills'
if (Test-Path $jskills) {
    Get-ChildItem $jskills -Directory | Where-Object { $_.Name -like '*aws*' -or $_.Name -like '*amazon*' } | Select-Object -ExpandProperty Name
} else { Write-Output 'no .jcode/skills dir' }
Write-Output '=== CLAUDE SKILLS DIR ==='
$cskills = Join-Path $env:USERPROFILE '.claude\skills'
if (Test-Path $cskills) {
    Get-ChildItem $cskills -Directory | Where-Object { $_.Name -like '*aws*' -or $_.Name -like '*amazon*' } | Select-Object -ExpandProperty Name
} else { Write-Output 'no .claude/skills dir' }
Write-Output '=== MCP CONFIG ==='
$mcpPaths = @(
    (Join-Path $env:USERPROFILE '.jcode\mcp.json'),
    (Join-Path $env:USERPROFILE '.claude.json'),
    (Join-Path $env:USERPROFILE '.aws\agent-toolkit\mcp.json')
)
foreach ($m in $mcpPaths) { if (Test-Path $m) { Write-Output "FOUND $m" } }
