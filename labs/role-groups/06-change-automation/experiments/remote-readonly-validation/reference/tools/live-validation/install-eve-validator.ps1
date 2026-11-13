[CmdletBinding()]
param(
    [string]$OperatorAlias = 'eve-operator',
    [string]$PublicKeyPath = (Join-Path $env:USERPROFILE '.ssh\codex_eve_validator_ed25519.pub'),
    [string]$OpenStackHost = '192.0.2.30',
    [int]$OpenStackSshPort = 22,
    [int]$OpenStackApiPort = 5000,
    [string]$ManagementPrefix = '192.0.2.',
    [switch]$RollbackArmed,
    [switch]$Apply
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ($OperatorAlias -notmatch '^[A-Za-z0-9._-]+$') {
    throw 'OperatorAlias contains unsupported characters.'
}
if (-not $Apply) {
    Write-Output 'DRY RUN: no remote changes were made. Re-run with -Apply -RollbackArmed after review.'
    exit 0
}
if (-not $RollbackArmed) {
    throw 'Refusing enforcement because the independently verified automatic rollback is not armed.'
}
if (-not (Test-Path -LiteralPath $PublicKeyPath -PathType Leaf)) {
    throw 'The dedicated EVE validator public key is missing.'
}

$publicKey = (Get-Content -LiteralPath $PublicKeyPath -Raw).Trim()
if ($publicKey -notmatch '^ssh-ed25519 [A-Za-z0-9+/=]+ codex-eve-validator$') {
    throw 'The public key does not match the dedicated EVE validator format.'
}

$remoteRoot = Join-Path $PSScriptRoot 'remote'
$dispatcher = Get-Content -LiteralPath (Join-Path $remoteRoot 'codex-eve-dispatcher.sh.example') -Raw
$validator = Get-Content -LiteralPath (Join-Path $remoteRoot 'validate-eve-readonly.sh.example') -Raw
$identityHelper = Get-Content -LiteralPath (Join-Path $remoteRoot 'validate-eve-identity-readonly.sh.example') -Raw
$sudoers = Get-Content -LiteralPath (Join-Path $remoteRoot 'eve-validator-sudoers.example') -Raw
$authorizedKey = Get-Content -LiteralPath (Join-Path $remoteRoot 'eve-validator-authorized-key.example') -Raw
$sshDropIn = Get-Content -LiteralPath (Join-Path $remoteRoot 'eve-validator-sshd.conf.example') -Raw

$validator = $validator.Replace('<OPENSTACK_MANAGEMENT_HOST>', $OpenStackHost)
$validator = $validator.Replace('<OPENSTACK_SSH_PORT>', [string]$OpenStackSshPort)
$validator = $validator.Replace('<OPENSTACK_API_PORT>', [string]$OpenStackApiPort)
$validator = $validator.Replace('<EVE_MANAGEMENT_SUBNET_PREFIX>', $ManagementPrefix)
$authorizedKey = $authorizedKey.Replace('<DEDICATED_EVE_VALIDATOR_PUBLIC_KEY>', $publicKey)

function ConvertTo-Base64([string]$Value) {
    [Convert]::ToBase64String([Text.UTF8Encoding]::new($false).GetBytes(($Value -replace "`r`n", "`n")))
}

$dispatcher64 = ConvertTo-Base64 $dispatcher
$validator64 = ConvertTo-Base64 $validator
$identityHelper64 = ConvertTo-Base64 $identityHelper
$sudoers64 = ConvertTo-Base64 $sudoers
$authorizedKey64 = ConvertTo-Base64 $authorizedKey
$sshDropIn64 = ConvertTo-Base64 $sshDropIn

$remoteScript = @"
set -euo pipefail
id codex-validator >/dev/null 2>&1 || { echo 'Existing dedicated validator account is required.' >&2; exit 3; }
getent group codex-validator >/dev/null 2>&1 || { echo 'Existing dedicated validator group is required.' >&2; exit 4; }
password_state=`$(passwd -S codex-validator | awk '{print `$2}')
case "`$password_state" in L|LK|NP) ;; *) echo 'Validator password must be locked.' >&2; exit 5 ;; esac
! id -nG codex-validator | tr ' ' '\n' | grep -Eq '^(sudo|wheel|docker|libvirt|libvirt-qemu|lxd)$'

tmpdir=`$(mktemp -d)
trap 'rm -rf "`$tmpdir"' EXIT
printf '%s' '$dispatcher64' | base64 -d > "`$tmpdir/dispatcher"
printf '%s' '$validator64' | base64 -d > "`$tmpdir/validator"
printf '%s' '$identityHelper64' | base64 -d > "`$tmpdir/identity-helper"
printf '%s' '$sudoers64' | base64 -d > "`$tmpdir/sudoers"
printf '%s' '$authorizedKey64' | base64 -d > "`$tmpdir/authorized_keys"
printf '%s' '$sshDropIn64' | base64 -d > "`$tmpdir/sshd-dropin"

bash -n "`$tmpdir/dispatcher"
bash -n "`$tmpdir/validator"
bash -n "`$tmpdir/identity-helper"
/usr/sbin/visudo -cf "`$tmpdir/sudoers"
cp /etc/ssh/sshd_config "`$tmpdir/sshd-test"
printf '\nInclude %s\n' "`$tmpdir/sshd-dropin" >> "`$tmpdir/sshd-test"
/usr/sbin/sshd -t -f "`$tmpdir/sshd-test"

backup=/var/backups/snsd-zero-trust/eve-validator-installer/`$(date -u +%Y%m%dT%H%M%SZ)
install -d -o root -g root -m 0700 "`$backup"
for source in /usr/local/sbin/codex-eve-dispatcher /usr/local/sbin/validate-eve-readonly /usr/local/sbin/validate-eve-identity-readonly /etc/sudoers.d/codex-eve-validator /etc/ssh/sshd_config.d/90-snsd-zero-trust-validator.conf /home/codex-validator/.ssh/authorized_keys; do
  if [ -e "`$source" ]; then
    cp -a "`$source" "`$backup/`$(printf '%s' "`$source" | tr '/' '_')"
  fi
done

install -d -o root -g codex-validator -m 0750 /home/codex-validator /home/codex-validator/.ssh
install -o root -g root -m 0755 "`$tmpdir/dispatcher" /usr/local/sbin/codex-eve-dispatcher
install -o root -g root -m 0755 "`$tmpdir/validator" /usr/local/sbin/validate-eve-readonly
install -o root -g root -m 0755 "`$tmpdir/identity-helper" /usr/local/sbin/validate-eve-identity-readonly
install -o root -g root -m 0440 "`$tmpdir/sudoers" /etc/sudoers.d/codex-eve-validator
install -o root -g root -m 0600 "`$tmpdir/sshd-dropin" /etc/ssh/sshd_config.d/90-snsd-zero-trust-validator.conf
install -o root -g codex-validator -m 0640 "`$tmpdir/authorized_keys" /home/codex-validator/.ssh/authorized_keys

bash -n /usr/local/sbin/codex-eve-dispatcher
bash -n /usr/local/sbin/validate-eve-readonly
bash -n /usr/local/sbin/validate-eve-identity-readonly
/usr/sbin/visudo -cf /etc/sudoers.d/codex-eve-validator
/usr/sbin/visudo -c
/usr/sbin/sshd -t
if systemctl is-active --quiet ssh; then
  systemctl reload ssh
elif systemctl is-active --quiet sshd; then
  systemctl reload sshd
else
  echo 'SSH service is not active.' >&2
  exit 6
fi
stat -c '%U %G %a %n' /usr/local/sbin/codex-eve-dispatcher /usr/local/sbin/validate-eve-readonly /usr/local/sbin/validate-eve-identity-readonly /etc/sudoers.d/codex-eve-validator /etc/ssh/sshd_config.d/90-snsd-zero-trust-validator.conf /home/codex-validator /home/codex-validator/.ssh /home/codex-validator/.ssh/authorized_keys
echo 'EVE bounded identity validator endpoint normalized.'
"@

$ssh = (Get-Command ssh -ErrorAction Stop).Source
$psi = New-Object Diagnostics.ProcessStartInfo
$psi.FileName = $ssh
$psi.Arguments = "-o BatchMode=yes -o ConnectTimeout=10 $OperatorAlias bash -s"
$psi.UseShellExecute = $false
$psi.RedirectStandardInput = $true
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$process = [Diagnostics.Process]::Start($psi)
$process.StandardInput.Write($remoteScript)
$process.StandardInput.Close()
$stdout = $process.StandardOutput.ReadToEnd()
$stderr = $process.StandardError.ReadToEnd()
$process.WaitForExit()
if ($stdout) { Write-Output $stdout.TrimEnd() }
if ($stderr) { Write-Error $stderr.TrimEnd() }
exit $process.ExitCode
