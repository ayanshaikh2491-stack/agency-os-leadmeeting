$env = Get-Content ".env.local" -ErrorAction SilentlyContinue
Write-Output "=== .env.local (masked) ==="
foreach ($line in $env) {
  if ($line -match '^[A-Za-z_][A-Za-z0-9_]*\s*=') {
    $name = ($line -split '=',2)[0]
    Write-Output "$name=***"
  } else {
    Write-Output $line
  }
}
Write-Output ""
Write-Output "=== .vercel/project.json ==="
if (Test-Path ".vercel\project.json") { Get-Content ".vercel\project.json" }
Write-Output ""
Write-Output "=== vercel whoami ==="
vercel whoami 2>&1
