$ErrorActionPreference = 'Continue'
$aws = Join-Path $env:LOCALAPPDATA 'Programs\Amazon\AWSCLIV2\aws.exe'
Write-Output '=== STS (auth works?) ==='
& $aws sts get-caller-identity --profile aws2 2>&1
Write-Output '=== ACCOUNT ATTRIBUTES (ec2) ==='
& $aws ec2 describe-account-attributes --region us-east-1 --profile aws2 2>&1
Write-Output '=== BILLING ACCOUNT STATUS (may fail without billing perms) ==='
& $aws account get-contact-information --profile aws2 2>&1 | Select-Object -First 10
Write-Output '=== TRY OTHER REGIONS quickly ==='
foreach ($reg in @('us-east-2','us-west-2','eu-west-1')) {
    $out = & $aws ec2 describe-regions --region $reg --profile aws2 2>&1 | Out-String
    if ($out -match 'OptInRequired') { Write-Output "$reg : OptInRequired" } elseif ($out -match 'error') { Write-Output "$reg : $($out.Trim().Split("`n")[0])" } else { Write-Output "$reg : OK" }
}
