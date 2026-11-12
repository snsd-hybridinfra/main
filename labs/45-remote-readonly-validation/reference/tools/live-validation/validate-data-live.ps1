[CmdletBinding()]
param([string]$OutputDirectory = '.runtime/zero-trust/data/latest')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$outputRoot = [IO.Path]::GetFullPath((Join-Path $repoRoot $OutputDirectory))
$runtimeBoundary = [IO.Path]::GetFullPath((Join-Path $repoRoot '.runtime\zero-trust\data'))
if (-not $outputRoot.StartsWith($runtimeBoundary, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Output must remain under .runtime/zero-trust/data/.'
}
[IO.Directory]::CreateDirectory($outputRoot) | Out-Null
$python = (Get-Command python -ErrorAction Stop).Source

$prerequisites = @(
    'docs\zero-trust\packages\zt-fnd-001-package.yaml',
    'docs\zero-trust\packages\zt-net-001-package.yaml',
    'docs\zero-trust\packages\zt-vis-001-package.yaml',
    'docs\zero-trust\packages\zt-id-001-package.yaml',
    'docs\zero-trust\packages\zt-dev-001-package.yaml',
    'docs\zero-trust\packages\zt-app-001-package.yaml'
)
foreach ($relative in $prerequisites) {
    if (-not [IO.File]::Exists((Join-Path $repoRoot $relative))) { throw "Missing prerequisite authority: $relative" }
}

& $python (Join-Path $repoRoot 'tools\data\validate_data_inventory.py') --verbose
if ($LASTEXITCODE -ne 0) { throw 'Data inventory and policy validation failed.' }

& $python (Join-Path $repoRoot 'tools\data\scan_data_policy.py') --self-test --verbose --output (Join-Path $outputRoot 'dlp-summary.json')
if ($LASTEXITCODE -ne 0) { throw 'Detection-only DLP validation failed.' }

& $python (Join-Path $repoRoot 'tools\data\validate_backup_assurance.py') --execute-controlled-fixture --verbose --output (Join-Path $outputRoot 'backup-test')
if ($LASTEXITCODE -ne 0) { throw 'Controlled synthetic backup and isolated restore validation failed.' }

$summary = [ordered]@{
    package_id = 'ZT-DATA-001'
    generated_at = [DateTime]::UtcNow.ToString('o')
    scope = 'REPOSITORY_GENERATED_EVIDENCE_SANITIZED_TELEMETRY_AND_SYNTHETIC_BACKUP_FIXTURE'
    inventory = 'PASS'
    classification = 'PASS'
    access_policy = 'PASS'
    data_flows = 'PASS'
    encryption_assessment = 'PASS_WITH_GAPS'
    dlp = 'DETECTION_ONLY_PASS'
    backup = 'SYNTHETIC_BACKUP_PASS'
    restore = 'SYNTHETIC_ISOLATED_RESTORE_PASS'
    source_overwritten = $false
    real_data_inspected = $false
    external_transmission = $false
    keys_or_credentials_rotated = $false
    blocking_dlp = $false
    runtime_ignored = $true
}
[IO.File]::WriteAllText((Join-Path $outputRoot 'data-live-summary.json'), ($summary | ConvertTo-Json -Depth 4), [Text.UTF8Encoding]::new($false))
Write-Output '[PASS] ZT-DATA-001 bounded data validation completed with detection-only DLP and isolated synthetic restore.'
exit 0
