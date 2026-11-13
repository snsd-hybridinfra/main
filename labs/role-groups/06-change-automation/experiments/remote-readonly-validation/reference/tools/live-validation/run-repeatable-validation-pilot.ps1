[CmdletBinding()]
param(
    [ValidateSet('Check','Plan','ExecuteReadOnly','Assess','AppendVerifiedExecution')]
    [string]$Mode = 'Check',
    [string]$CampaignId = 'ZT-RV-001',
    [string]$AssessmentTime,
    [string]$OutputDirectory = '.runtime/zero-trust/repeatable-validation',
    [string]$CandidateExecution,
    [string]$ApprovalReference,
    [switch]$VerboseOutput
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if($CampaignId -ne 'ZT-RV-001'){throw 'Only the fixed ZT-RV-001 campaign is allowed.'}
$repoRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$outputRoot=[IO.Path]::GetFullPath((Join-Path $repoRoot $OutputDirectory))
$boundary=[IO.Path]::GetFullPath((Join-Path $repoRoot '.runtime\zero-trust\repeatable-validation'))
if(-not $outputRoot.StartsWith($boundary,[StringComparison]::OrdinalIgnoreCase)){throw 'Output must remain under the ignored repeatable-validation runtime boundary.'}
$python=(Get-Command python -ErrorAction Stop).Source
$script=Join-Path $repoRoot 'tools\continuous_verification\run_repeatability_campaign.py'
$arguments=@($script)
switch($Mode){
 'Check'{$arguments+='--check'}
 'Plan'{$arguments+='--plan'}
 'ExecuteReadOnly'{$arguments+='--execute-read-only'}
 'Assess'{$arguments+='--assess';if($AssessmentTime){$arguments+=@('--assessment-time',$AssessmentTime)}}
 'AppendVerifiedExecution'{
   if(-not $CandidateExecution){throw 'AppendVerifiedExecution requires -CandidateExecution.'}
   $append=@((Join-Path $repoRoot 'tools\continuous_verification\append_verified_execution.py'),'--candidate',$CandidateExecution,'--check')
   & $python @append
   if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
   Write-Output '[INFO] Check passed. Use the explicit Python --append mode with an approval reference after reviewing the proposed diff.'
   exit 0
 }
}
if($VerboseOutput){$arguments+='--verbose'}
& $python @arguments
exit $LASTEXITCODE
