$ErrorActionPreference = "Stop"
$base = Join-Path $PSScriptRoot "pocketbase"
New-Item -ItemType Directory -Force -Path $base | Out-Null
$zip = Join-Path $base "pb-win.zip"
Invoke-WebRequest -Uri "https://github.com/pocketbase/pocketbase/releases/download/v0.39.10/pocketbase_0.39.10_windows_amd64.zip" -OutFile $zip -TimeoutSec 180
Expand-Archive -Path $zip -DestinationPath (Join-Path $base "win") -Force
Get-ChildItem (Join-Path $base "win")
Write-Output "DONE"
