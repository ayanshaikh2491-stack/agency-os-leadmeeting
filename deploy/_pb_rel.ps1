$ErrorActionPreference = "Stop"
$r = Invoke-RestMethod -Uri "https://api.github.com/repos/pocketbase/pocketbase/releases/latest" -Headers @{"User-Agent"="jcode"} -TimeoutSec 30
Write-Output ("tag: " + $r.tag_name)
foreach ($a in $r.assets) {
  if ($a.name -match "(windows_amd64|linux_amd64)") {
    Write-Output ($a.name + "  " + $a.browser_download_url)
  }
}
