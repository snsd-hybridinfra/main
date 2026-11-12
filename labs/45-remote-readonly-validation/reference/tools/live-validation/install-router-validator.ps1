[CmdletBinding()]
param(
    [string]$OperatorAlias = 'eve-operator',
    [string]$PublicKeyPath = (Join-Path $HOME '.ssh\codex_router_validator_ed25519.pub'),
    [Parameter(Mandatory)][int]$ConsolePort,
    [Parameter(Mandatory)][ValidatePattern('^(?:\d{1,3}\.){3}\d{1,3}$')][string]$OpenStackRouterExternalIp,
    [Parameter(Mandatory)][ValidatePattern('^(?:\d{1,3}\.){3}\d{1,3}$')][string]$OpenStackFloatingIp,
    [switch]$Apply
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($ConsolePort -lt 1024 -or $ConsolePort -gt 65535) { throw 'ConsolePort is outside the expected range.' }
if (-not $Apply) { Write-Output 'DRY RUN: no remote changes were made. Re-run with -Apply after review.'; exit 0 }
if (-not (Test-Path -LiteralPath $PublicKeyPath -PathType Leaf)) { throw 'Dedicated router validator public key is missing.' }
$publicKey = (Get-Content -LiteralPath $PublicKeyPath -Raw).Trim()
if ($publicKey -notmatch '^ssh-ed25519 [A-Za-z0-9+/=]+ codex-router-validator$') { throw 'Unexpected dedicated router validator public-key format.' }

$remoteRoot = Join-Path $PSScriptRoot 'remote'
$dispatcher = Get-Content (Join-Path $remoteRoot 'codex-router-dispatcher.sh.example') -Raw
$validator = Get-Content (Join-Path $remoteRoot 'validate-snsd-r1-readonly.sh.example') -Raw
$sudoers = Get-Content (Join-Path $remoteRoot 'router-validator-sudoers.example') -Raw
$authorizedKey = Get-Content (Join-Path $remoteRoot 'router-validator-authorized-key.example') -Raw
$validator = $validator.Replace('<ROUTER_CONSOLE_PORT>', [string]$ConsolePort).Replace('<OPENSTACK_ROUTER_EXTERNAL_IP>', $OpenStackRouterExternalIp).Replace('<OPENSTACK_FLOATING_IP>', $OpenStackFloatingIp)
$authorizedKey = $authorizedKey.Replace('<DEDICATED_ROUTER_VALIDATOR_PUBLIC_KEY>', $publicKey)

function ConvertTo-Base64([string]$Value) { [Convert]::ToBase64String([Text.UTF8Encoding]::new($false).GetBytes(($Value -replace "`r`n", "`n"))) }
$d64=ConvertTo-Base64 $dispatcher; $v64=ConvertTo-Base64 $validator; $s64=ConvertTo-Base64 $sudoers; $a64=ConvertTo-Base64 $authorizedKey
$remoteScript = @"
set -euo pipefail
id codex-router-validator >/dev/null 2>&1 || useradd --create-home --shell /bin/bash codex-router-validator
install -d -o codex-router-validator -g codex-router-validator -m 0700 /home/codex-router-validator/.ssh
tmpdir=`$(mktemp -d); trap 'rm -rf "`$tmpdir"' EXIT
printf '%s' '$d64' | base64 -d > "`$tmpdir/dispatcher"
printf '%s' '$v64' | base64 -d > "`$tmpdir/validator"
printf '%s' '$s64' | base64 -d > "`$tmpdir/sudoers"
printf '%s' '$a64' | base64 -d > "`$tmpdir/authorized_keys"
bash -n "`$tmpdir/dispatcher"; bash -n "`$tmpdir/validator"; /usr/sbin/visudo -cf "`$tmpdir/sudoers"
install -o root -g root -m 0755 "`$tmpdir/dispatcher" /usr/local/sbin/codex-router-dispatcher
install -o root -g root -m 0755 "`$tmpdir/validator" /usr/local/sbin/validate-snsd-r1-readonly
install -o root -g root -m 0440 "`$tmpdir/sudoers" /etc/sudoers.d/codex-router-validator
install -o codex-router-validator -g codex-router-validator -m 0600 "`$tmpdir/authorized_keys" /home/codex-router-validator/.ssh/authorized_keys
bash -n /usr/local/sbin/codex-router-dispatcher; bash -n /usr/local/sbin/validate-snsd-r1-readonly; /usr/sbin/visudo -cf /etc/sudoers.d/codex-router-validator
stat -c '%U %G %a %n' /usr/local/sbin/codex-router-dispatcher /usr/local/sbin/validate-snsd-r1-readonly /etc/sudoers.d/codex-router-validator /home/codex-router-validator/.ssh/authorized_keys
"@
$ssh=(Get-Command ssh -ErrorAction Stop).Source
$psi=[Diagnostics.ProcessStartInfo]::new(); $psi.FileName=$ssh; $psi.Arguments="-o BatchMode=yes -o ConnectTimeout=10 $OperatorAlias bash -s"; $psi.UseShellExecute=$false; $psi.RedirectStandardInput=$true; $psi.RedirectStandardOutput=$true; $psi.RedirectStandardError=$true
$process=[Diagnostics.Process]::Start($psi); $process.StandardInput.Write($remoteScript); $process.StandardInput.Close(); $stdout=$process.StandardOutput.ReadToEnd(); $stderr=$process.StandardError.ReadToEnd(); $process.WaitForExit()
if($stdout){Write-Output $stdout.TrimEnd()}; if($stderr){Write-Error $stderr.TrimEnd()}; exit $process.ExitCode
