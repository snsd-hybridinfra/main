[CmdletBinding()]
param(
    [string]$WorkflowId = 'ZTA-WF-VAL-001',
    [ValidateSet('Check', 'Plan', 'ExecuteReadOnly', 'ProposalOnly')]
    [string]$Mode = 'Check',
    [string]$OutputDirectory = '.runtime/zero-trust/automation/foundation',
    [switch]$VerboseOutput
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$outputRoot = [IO.Path]::GetFullPath((Join-Path $repoRoot $OutputDirectory))
$runtimeBoundary = [IO.Path]::GetFullPath((Join-Path $repoRoot '.runtime\zero-trust\automation'))
if (-not $outputRoot.StartsWith($runtimeBoundary, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Output must remain under .runtime/zero-trust/automation/.'
}
[IO.Directory]::CreateDirectory($outputRoot) | Out-Null
$python = (Get-Command python -ErrorAction Stop).Source

& $python (Join-Path $repoRoot 'tools\automation\validate_automation_catalogs.py') --verbose
if ($LASTEXITCODE -ne 0) { throw 'Automation catalog validation failed.' }

$modeValue = switch ($Mode) {
    'Check' { 'CHECK' }
    'Plan' { 'PLAN' }
    'ExecuteReadOnly' { 'EXECUTE_READ_ONLY' }
    'ProposalOnly' { 'PROPOSAL_ONLY' }
}
& $python (Join-Path $repoRoot 'tools\automation\evaluate_action_policy.py') --workflow $WorkflowId --mode $modeValue --verbose
$policyExit = $LASTEXITCODE
if ($policyExit -ne 0) { throw 'Automation policy denied the requested workflow.' }

$planPath = Join-Path $outputRoot "$WorkflowId-$($Mode.ToLowerInvariant())-plan.json"
& $python (Join-Path $repoRoot 'tools\automation\plan_workflow.py') --workflow $WorkflowId --mode $modeValue --format json --output $planPath
if ($LASTEXITCODE -ne 0) { throw 'Deterministic workflow planning failed.' }

$runnerMode = switch ($Mode) {
    'Check' { '--check' }
    'Plan' { '--plan' }
    'ExecuteReadOnly' { '--execute-read-only' }
    'ProposalOnly' { '--proposal-only' }
}
$runnerArguments = @((Join-Path $repoRoot 'tools\automation\run_workflow.py'), $runnerMode, '--workflow', $WorkflowId)
if ($VerboseOutput) { $runnerArguments += '--verbose' }
& $python @runnerArguments
$runnerExit = $LASTEXITCODE

$summary = [ordered]@{
    package_id = 'ZT-AUTO-001'
    generated_at = [DateTime]::UtcNow.ToString('o')
    workflow_id = $WorkflowId
    requested_mode = $Mode
    policy_evaluated = $true
    deterministic_plan_created = $true
    runner_exit_code = $runnerExit
    mutation_action_executed = $false
    arbitrary_command_accepted = $false
    authoritative_document_updated = $false
    external_notification_sent = $false
    credentials_printed = $false
    runtime_ignored = $true
}
[IO.File]::WriteAllText((Join-Path $outputRoot 'automation-foundation-summary.json'), ($summary | ConvertTo-Json -Depth 4), [Text.UTF8Encoding]::new($false))
if ($runnerExit -ne 0) { exit $runnerExit }
Write-Output "[PASS] ZT-AUTO-001 $Mode completed through the fixed-handler, no-mutation boundary."
exit 0
