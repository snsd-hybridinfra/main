[CmdletBinding()]
param(
    [string]$OutputDirectory = ".runtime/zero-trust/eve"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
$outputRoot = [IO.Path]::GetFullPath((Join-Path $root $OutputDirectory))
[IO.Directory]::CreateDirectory($outputRoot) | Out-Null
$stamp = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssZ")
$rawPath = Join-Path $outputRoot "$stamp-eve.raw.txt"
$sanitizedPath = Join-Path $outputRoot "$stamp-eve.sanitized.txt"

$ssh = Get-Command ssh -ErrorAction Stop
$psi = New-Object Diagnostics.ProcessStartInfo
$psi.FileName = $ssh.Source
$psi.Arguments = '-o BatchMode=yes -o ConnectTimeout=10 eve-validator validate-host'
$psi.UseShellExecute = $false
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$process = [Diagnostics.Process]::Start($psi)
$captured = $process.StandardOutput.ReadToEnd() + $process.StandardError.ReadToEnd()
$process.WaitForExit()
$remoteExitCode = $process.ExitCode
[IO.File]::WriteAllText($rawPath, $captured, [Text.UTF8Encoding]::new($false))

$python = Get-Command python -ErrorAction Stop
& $python.Source (Join-Path $PSScriptRoot 'sanitize-live-evidence.py') --input $rawPath --output $sanitizedPath | Out-Null
Write-Output "Sanitized evidence: $sanitizedPath"
exit $remoteExitCode
