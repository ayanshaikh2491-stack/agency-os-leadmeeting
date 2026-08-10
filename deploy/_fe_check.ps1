$ErrorActionPreference = "Continue"
$urls = @(
  "https://agency-frontend-seven.vercel.app/",
  "https://agency-frontend-seven.vercel.app/admin",
  "https://agency-frontend-seven.vercel.app/api/health",
  "https://agency-frontend-seven.vercel.app/login"
)
foreach ($u in $urls) {
  Write-Output "=== $u ==="
  try {
    $r = Invoke-WebRequest -Uri $u -MaximumRedirection 0 -SkipHttpErrorCheck -TimeoutSec 25 -Headers @{"User-Agent"="Mozilla/5.0"}
    Write-Output ("status: " + [int]$r.StatusCode)
    if ($r.Headers.Location) { Write-Output ("location: " + $r.Headers.Location) }
    $len = $r.RawContentLength
    Write-Output ("bytes: " + $len)
    $ct = $r.Headers."Content-Type"
    Write-Output ("type: " + $ct)
    if ($r.StatusCode -eq 200) {
      $body = $r.Content
      if ($body.Length -gt 600) { $body = $body.Substring(0,600) }
      Write-Output $body
    }
  } catch {
    Write-Output ("ERR: " + $_.Exception.Message)
  }
  Write-Output ""
}
