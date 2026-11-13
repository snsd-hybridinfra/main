[CmdletBinding()]
param(
    [ValidateSet('Check','Plan','ExecuteReadOnly','Assess')]
    [string]$Mode = 'Check',
    [string]$AssessmentTime,
    [switch]$VerboseOutput
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$python = (Get-Command python -ErrorAction Stop).Source
$script = Join-Path $repoRoot 'tools\continuous_verification\run_scheduled_validation.py'
$arguments = @($script)
switch ($Mode) {
    'Check' { $arguments += '--check' }
    'Plan' { $arguments += '--plan' }
    'ExecuteReadOnly' { $arguments += '--execute-read-only' }
    'Assess' {
        $arguments += '--assess'
        if ($AssessmentTime) { $arguments += @('--assessment-time', $AssessmentTime) }
    }
}
if ($VerboseOutput) { $arguments += '--verbose' }
& $python @arguments
exit $LASTEXITCODE
