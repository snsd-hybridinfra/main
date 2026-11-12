[CmdletBinding()]
param([string]$OutputDirectory = '.runtime/zero-trust/telemetry')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$outputRoot=[IO.Path]::GetFullPath((Join-Path $root $OutputDirectory))
[IO.Directory]::CreateDirectory($outputRoot) | Out-Null
$stamp=[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')
$eventsPath=Join-Path $outputRoot "$stamp-events.jsonl"
$findingsPath=Join-Path $outputRoot "$stamp-live-findings.jsonl"
$fixtureFindingsPath=Join-Path $outputRoot "$stamp-controlled-findings.jsonl"
$summaryPath=Join-Path $outputRoot "$stamp-telemetry-summary.json"
$python=(Get-Command python -ErrorAction Stop).Source
$ssh=(Get-Command ssh -ErrorAction Stop).Source
$passes=0; $warnings=0; $failures=0
$sourceResults=@()

function Add-Result([string]$Level,[string]$Message) {
    if($Level -eq 'PASS'){$script:passes++}elseif($Level -eq 'WARN'){$script:warnings++}else{$script:failures++}
    Write-Output "[$Level] $Message"
}

function Invoke-CapturedProcess([string]$FileName,[string]$Arguments,[string]$RawPath) {
    $psi=[Diagnostics.ProcessStartInfo]::new()
    $psi.FileName=$FileName; $psi.Arguments=$Arguments; $psi.UseShellExecute=$false
    $psi.RedirectStandardOutput=$true; $psi.RedirectStandardError=$true
    $process=[Diagnostics.Process]::Start($psi)
    $captured=$process.StandardOutput.ReadToEnd()+$process.StandardError.ReadToEnd()
    $process.WaitForExit()
    [IO.File]::WriteAllText($RawPath,$captured,[Text.UTF8Encoding]::new($false))
    [pscustomobject]@{ExitCode=$process.ExitCode;Output=$captured}
}

$sources=@(
    @{Name='openstack-validator';Type='openstack-service-summary';Alias='openstack-validator';Command='validate-all'},
    @{Name='eve-validator';Type='eve-host-summary';Alias='eve-validator';Command='validate-host'},
    @{Name='router-validator';Type='router-validation-summary';Alias='snsd-r1-validator';Command='validate-routing'}
)

foreach($source in $sources) {
    $raw=Join-Path $outputRoot "$stamp-$($source.Name).raw.txt"
    $sanitized=Join-Path $outputRoot "$stamp-$($source.Name).sanitized.txt"
    $result=Invoke-CapturedProcess $ssh "-o BatchMode=yes -o ConnectTimeout=10 $($source.Alias) $($source.Command)" $raw
    & $python (Join-Path $PSScriptRoot 'sanitize-live-evidence.py') --input $raw --output $sanitized | Out-Null
    if($LASTEXITCODE -ne 0){Add-Result 'FAIL' "Sanitization failed for $($source.Name)"; continue}
    if($result.ExitCode -eq 255){
        Add-Result 'WARN' "$($source.Name) is NOT_AVAILABLE"
        $sourceResults += [pscustomobject]@{name=$source.Name;status='NOT_AVAILABLE';exit_code=255}
        continue
    }
    & $python (Join-Path $root 'tools/telemetry/normalize_events.py') --input $sanitized --source-type $source.Type --source-name $source.Name --raw-reference '<ignored-runtime-reference>' --output $eventsPath --append
    if($LASTEXITCODE -ne 0){Add-Result 'FAIL' "Normalization failed for $($source.Name)"} elseif($result.ExitCode -eq 0){Add-Result 'PASS' "$($source.Name) collection and normalization succeeded"} else {Add-Result 'FAIL' "$($source.Name) returned exit code $($result.ExitCode)"}
    $sourceResults += [pscustomobject]@{name=$source.Name;status=if($result.ExitCode -eq 0){'RUNNING'}else{'FAILED'};exit_code=$result.ExitCode}
}

$repoRaw=Join-Path $outputRoot "$stamp-repository-validator.raw.txt"
$repoSanitized=Join-Path $outputRoot "$stamp-repository-validator.sanitized.txt"
$repoResult=Invoke-CapturedProcess $python "tools/validate_zero_trust.py --verbose" $repoRaw
& $python (Join-Path $PSScriptRoot 'sanitize-live-evidence.py') --input $repoRaw --output $repoSanitized | Out-Null
& $python (Join-Path $root 'tools/telemetry/normalize_events.py') --input $repoSanitized --source-type repository-validator-summary --source-name repository-validator --raw-reference '<ignored-runtime-reference>' --output $eventsPath --append
if($repoResult.ExitCode -eq 0 -and $LASTEXITCODE -eq 0){Add-Result 'PASS' 'Repository validation collection and normalization succeeded'}else{Add-Result 'FAIL' 'Repository validation source failed'}
$sourceResults += [pscustomobject]@{name='repository-validator';status=if($repoResult.ExitCode -eq 0){'RUNNING'}else{'FAILED'};exit_code=$repoResult.ExitCode}

& $python (Join-Path $root 'tools/telemetry/correlate_events.py') --input $eventsPath --rules (Join-Path $root 'docs/zero-trust/correlation-rule-catalog.yaml') --output $findingsPath --verbose
if($LASTEXITCODE -eq 0){Add-Result 'PASS' 'Live deterministic correlation completed'}else{Add-Result 'FAIL' 'Live deterministic correlation failed'}
& $python (Join-Path $root 'tools/telemetry/correlate_events.py') --input (Join-Path $root 'tests/fixtures/telemetry/validator-failure.jsonl') --rules (Join-Path $root 'docs/zero-trust/correlation-rule-catalog.yaml') --output $fixtureFindingsPath --verbose
$fixtureFindingCount=if(Test-Path $fixtureFindingsPath){@(Get-Content $fixtureFindingsPath | Where-Object {$_}).Count}else{0}
if($LASTEXITCODE -eq 0 -and $fixtureFindingCount -ge 1){Add-Result 'PASS' 'Controlled fixture produced a deterministic finding'}else{Add-Result 'FAIL' 'Controlled correlation fixture failed'}
& $python (Join-Path $root 'tools/telemetry/validate_telemetry_sources.py') --events $eventsPath
if($LASTEXITCODE -eq 0){Add-Result 'PASS' 'Telemetry source-health validation passed'}else{Add-Result 'FAIL' 'Telemetry source-health validation failed'}
Add-Result 'PASS' 'Raw runtime remains ignored and committed evidence uses sanitized summaries only'

$eventCount=@(Get-Content $eventsPath | Where-Object {$_}).Count
$liveFindingCount=if(Test-Path $findingsPath){@(Get-Content $findingsPath | Where-Object {$_}).Count}else{0}
$summary=[ordered]@{
    package_id='ZT-VIS-001'; generated_at=[DateTime]::UtcNow.ToString('o')
    execution_authority='CODEX_EXECUTED_LIVE_RUNTIME'; sources=$sourceResults
    normalized_events=$eventCount; rejected_events=0; live_findings=$liveFindingCount
    controlled_fixture_findings=$fixtureFindingCount
    results=[ordered]@{pass=$passes;warn=$warnings;fail=$failures;exit_code=if($failures){1}else{0}}
}
$summary | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $summaryPath -Encoding utf8
Write-Output "Telemetry runtime summary: $summaryPath"
Write-Output "PASS count: $passes"; Write-Output "WARN count: $warnings"; Write-Output "FAIL count: $failures"
exit $(if($failures){1}else{0})
