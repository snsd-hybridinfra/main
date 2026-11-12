[CmdletBinding()]
param([string]$OutputDirectory = '.runtime/zero-trust/application/latest')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$outputRoot = [IO.Path]::GetFullPath((Join-Path $repoRoot $OutputDirectory))
[IO.Directory]::CreateDirectory($outputRoot) | Out-Null
$python = (Get-Command python -ErrorAction Stop).Source

& $python (Join-Path $repoRoot 'tools\application\validate_application_inventory.py') --verbose
if ($LASTEXITCODE -ne 0) { throw 'Application inventory validation failed.' }
& $python (Join-Path $repoRoot 'tools\application\run_security_scans.py') --check --verbose --output (Join-Path $outputRoot 'scans')
if ($LASTEXITCODE -ne 0) { throw 'Application security scans failed.' }
& $python (Join-Path $repoRoot 'tools\application\validate_secure_deployment.py') --verbose
if ($LASTEXITCODE -ne 0) { throw 'Secure deployment validation failed.' }

$windowsPowerShell = (Get-Command powershell -ErrorAction Stop).Source
$runtimeOutput = & $windowsPowerShell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'manage-persistent-telemetry.ps1') -Mode Validate 2>&1
$runtimeExit = $LASTEXITCODE
[IO.File]::WriteAllLines((Join-Path $outputRoot 'pilot-runtime.raw.txt'), [string[]]$runtimeOutput, [Text.UTF8Encoding]::new($false))
if ($runtimeExit -ne 0) { throw 'Existing Alloy pilot runtime health validation failed.' }

$summary = [ordered]@{
    package_id = 'ZT-APP-001'
    generated_at = [DateTime]::UtcNow.ToString('o')
    pilot_application = 'ZTA-APP-OBSERVABILITY-STACK'
    pilot_workload = 'ZTA-WORKLOAD-ALLOY'
    inventory = 'PASS'
    security_scans = 'PASS'
    secure_deployment = 'PASS_WITH_WARNINGS'
    runtime_health = 'PASS'
    deployment_performed = $false
    workload_restarted = $false
    credentials_printed = $false
    raw_runtime_ignored = $true
}
[IO.File]::WriteAllText((Join-Path $outputRoot 'application-live-summary.json'), ($summary | ConvertTo-Json -Depth 4), [Text.UTF8Encoding]::new($false))
Write-Output '[PASS] ZT-APP-001 bounded live validation completed without deployment or restart.'
exit 0
