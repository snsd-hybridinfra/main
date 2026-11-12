[CmdletBinding()]
param(
    [ValidateSet('Check', 'Plan', 'ExecuteReadOnly', 'ProposalOnly')]
    [string]$Mode = 'Check',
    [string]$OutputDirectory = '.runtime/zero-trust/continuous-verification/cycles',
    [switch]$VerboseOutput
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$outputRoot = [IO.Path]::GetFullPath((Join-Path $repoRoot $OutputDirectory))
$runtimeBoundary = [IO.Path]::GetFullPath((Join-Path $repoRoot '.runtime\zero-trust\continuous-verification'))
if (-not $outputRoot.StartsWith($runtimeBoundary, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Output must remain under .runtime/zero-trust/continuous-verification/.'
}
[IO.Directory]::CreateDirectory($outputRoot) | Out-Null
$python = (Get-Command python -ErrorAction Stop).Source

& $python (Join-Path $repoRoot 'tools\continuous_verification\validate_verification_configuration.py') --verbose
if ($LASTEXITCODE -ne 0) { throw 'Continuous verification configuration validation failed.' }

$automationOutput = '.runtime/zero-trust/automation/continuous-verification'
$arguments = @(
    '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
    (Join-Path $repoRoot 'tools\live-validation\run-automation-foundation.ps1'),
    '-WorkflowId', 'ZT-CV-WF-001', '-Mode', $Mode,
    '-OutputDirectory', $automationOutput
)
if ($VerboseOutput) { $arguments += '-VerboseOutput' }
& powershell @arguments
$cycleExit = $LASTEXITCODE

$summary = [ordered]@{
    package_id = 'ZT-CV-001'
    generated_at = [DateTime]::UtcNow.ToString('o')
    workflow_id = 'ZT-CV-WF-001'
    requested_mode = $Mode
    runner_exit_code = $cycleExit
    one_time_cycle_only = $true
    scheduled_trigger = $false
    schedule_installed = $false
    continuous_observation_claimed = $false
    continuous_enforcement_claimed = $false
    automatic_remediation_performed = $false
    authoritative_document_updated = $false
    maturity_assigned = $false
    runtime_ignored = $true
}
[IO.File]::WriteAllText((Join-Path $outputRoot 'continuous-verification-summary.json'), ($summary | ConvertTo-Json -Depth 4), [Text.UTF8Encoding]::new($false))
if ($cycleExit -ne 0) { exit $cycleExit }
Write-Output "[PASS] ZT-CV-001 $Mode completed through the manual, fixed-handler, no-mutation boundary."
exit 0
