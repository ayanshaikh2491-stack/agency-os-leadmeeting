$ErrorActionPreference = 'Stop'
Write-Output '=== Checking connectivity to awscli.amazonaws.com ==='
try {
    $r = Invoke-WebRequest -Uri 'https://awscli.amazonaws.com' -Method Head -TimeoutSec 15
    Write-Output ("Connectivity OK: " + $r.StatusCode)
} catch {
    Write-Output ("NETWORK FAIL: " + $_.Exception.Message)
    exit 1
}
Write-Output '=== Installing AWS CLI v2 (user-local) ==='
try {
    irm 'https://awscli.amazonaws.com/v2/install.ps1' | iex
} catch {
    Write-Output ("INSTALL FAIL: " + $_.Exception.Message)
    exit 1
}
Write-Output '=== Locating aws.exe ==='
$candidates = @(
    "$env:LOCALAPPDATA\Programs\Amazon\AWSCLIV2\aws.exe",
    "$env:ProgramFiles\Amazon\AWSCLIV2\aws.exe"
)
$found = $null
foreach ($c in $candidates) {
    if (Test-Path $c) { $found = $c; break }
}
if (-not $found) {
    Write-Output 'aws.exe NOT found in standard paths'
    exit 1
}
Write-Output ("Found: " + $found)
& $found --version
