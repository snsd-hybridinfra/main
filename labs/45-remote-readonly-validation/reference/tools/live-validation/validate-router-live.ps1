[CmdletBinding()]
param([string]$OutputDirectory = '.runtime/zero-trust/router')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$outputRoot=[IO.Path]::GetFullPath((Join-Path $root $OutputDirectory)); [IO.Directory]::CreateDirectory($outputRoot) | Out-Null
$stamp=[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')
$rawPath=Join-Path $outputRoot "$stamp-router.raw.txt"; $sanitizedPath=Join-Path $outputRoot "$stamp-router.sanitized.txt"
$ssh=(Get-Command ssh -ErrorAction Stop).Source
$psi=[Diagnostics.ProcessStartInfo]::new(); $psi.FileName=$ssh; $psi.Arguments='-o BatchMode=yes -o ConnectTimeout=10 snsd-r1-validator validate-routing'; $psi.UseShellExecute=$false; $psi.RedirectStandardOutput=$true; $psi.RedirectStandardError=$true
$process=[Diagnostics.Process]::Start($psi); $captured=$process.StandardOutput.ReadToEnd()+$process.StandardError.ReadToEnd(); $process.WaitForExit(); $remoteExitCode=$process.ExitCode
[IO.File]::WriteAllText($rawPath,$captured,[Text.UTF8Encoding]::new($false))
$python=(Get-Command python -ErrorAction Stop).Source
& $python (Join-Path $PSScriptRoot 'sanitize-live-evidence.py') --input $rawPath --output $sanitizedPath | Out-Null
Write-Output "Sanitized evidence: $sanitizedPath"
exit $remoteExitCode
