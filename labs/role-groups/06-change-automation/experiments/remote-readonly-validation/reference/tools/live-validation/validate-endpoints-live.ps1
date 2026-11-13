[CmdletBinding()]
param(
    [string]$OutputDirectory = '.runtime/zero-trust/endpoint/latest',
    [switch]$SkipInfrastructureValidators
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$outputRoot = [IO.Path]::GetFullPath((Join-Path $repoRoot $OutputDirectory))
[IO.Directory]::CreateDirectory($outputRoot) | Out-Null
$keyPath = Join-Path $HOME '.ssh\codex_monitoring_operator_ed25519'
$knownHosts = Join-Path $HOME '.ssh\known_hosts_snsd_monitoring'
$openStack = 'sudo -n env OS_CLIENT_CONFIG_FILE=/etc/kolla/clouds.yaml /opt/openstack-client/bin/openstack --os-cloud kolla-admin'
$portName = 'snsd-monitoring-01-port'

foreach ($path in @($keyPath, $knownHosts)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Required monitoring access file is missing: $path"
    }
}

$foundationExit = $null
if (-not $SkipInfrastructureValidators) {
    $foundationOutput = Join-Path $OutputDirectory 'infrastructure'
    $foundationLog = Join-Path $outputRoot 'infrastructure-validation.raw.txt'
    $windowsPowerShell = (Get-Command powershell -ErrorAction Stop).Source
    $captured = & $windowsPowerShell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'run-foundation-validation.ps1') -OutputDirectory $foundationOutput 2>&1
    $foundationExit = $LASTEXITCODE
    [IO.File]::WriteAllLines($foundationLog, [string[]]$captured, [Text.UTF8Encoding]::new($false))
    Write-Output "[INFO] Existing restricted-validator aggregate exit code: $foundationExit"
}

$fixedIps = (& ssh -o BatchMode=yes openstack-operator "$openStack port show $portName -f value -c fixed_ips").Trim()
if ($LASTEXITCODE -ne 0) { throw 'Unable to resolve the monitoring VM address.' }
$vmIp = [regex]::Match($fixedIps, '(?<![0-9])(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?![0-9])').Value
$networkId = (& ssh -o BatchMode=yes openstack-operator "$openStack port show $portName -f value -c network_id").Trim()
if ($LASTEXITCODE -ne 0 -or -not $vmIp -or -not $networkId) { throw 'Unable to resolve the monitoring VM target scope.' }

$namespace = "qdhcp-$networkId"
$proxyCommand = "ssh -o BatchMode=yes openstack-operator sudo -n ip netns exec $namespace /usr/bin/nc %h %p"
$sshArgs = @(
    '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', '-o', 'IdentitiesOnly=yes',
    '-i', $keyPath, '-o', 'StrictHostKeyChecking=yes', '-o', "UserKnownHostsFile=$knownHosts",
    '-o', "ProxyCommand=$proxyCommand", "ubuntu@$vmIp"
)

$remoteScript = @'
set -u
. /etc/os-release
package_manager_error=false
if upgrade_output="$(apt list --upgradable 2>/dev/null)"; then
  security_updates="$(printf '%s\n' "$upgrade_output" | grep -c -- '-security' || true)"
else
  security_updates=0
  package_manager_error=true
fi
package_count="$(dpkg-query -W -f='${binary:Package}\n' 2>/dev/null | wc -l | tr -d ' ')"
container_runtime="$(docker --version 2>/dev/null || printf 'NOT_INSTALLED')"
compose_runtime="$(docker compose version 2>/dev/null || printf 'NOT_INSTALLED')"
running_containers="$(sudo -n docker ps -q 2>/dev/null | wc -l | tr -d ' ')"
if test -e /var/run/reboot-required; then reboot_required=true; else reboot_required=false; fi
agent_state=NOT_INSTALLED
for unit in wazuh-agent osqueryd falco; do
  if systemctl is-active --quiet "$unit" 2>/dev/null; then agent_state=EXISTING_HEALTHY; break; fi
done
printf 'OS_FAMILY=%s\n' "$ID"
printf 'OS_RELEASE=%s\n' "$VERSION_ID"
printf 'KERNEL=%s\n' "$(uname -r)"
printf 'PACKAGE_COUNT=%s\n' "$package_count"
printf 'CONTAINER_RUNTIME=%s\n' "$container_runtime"
printf 'COMPOSE_RUNTIME=%s\n' "$compose_runtime"
printf 'RUNNING_CONTAINER_COUNT=%s\n' "$running_containers"
printf 'SECURITY_UPDATES_AVAILABLE=%s\n' "$security_updates"
printf 'REBOOT_REQUIRED=%s\n' "$reboot_required"
printf 'PACKAGE_MANAGER_ERROR=%s\n' "$package_manager_error"
printf 'ENDPOINT_AGENT_STATE=%s\n' "$agent_state"
'@
$encoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($remoteScript))
$remoteOutput = & ssh @sshArgs "printf '%s' '$encoded' | base64 -d | bash"
if ($LASTEXITCODE -ne 0) { throw 'Fixed read-only endpoint collection failed.' }

$rawTextPath = Join-Path $outputRoot 'monitoring-vm.raw.txt'
[IO.File]::WriteAllLines($rawTextPath, [string[]]$remoteOutput, [Text.UTF8Encoding]::new($false))
$values = @{}
foreach ($line in $remoteOutput) {
    $parts = [string]$line -split '=', 2
    if ($parts.Count -eq 2) { $values[$parts[0]] = $parts[1] }
}
$required = @('OS_FAMILY','OS_RELEASE','KERNEL','PACKAGE_COUNT','CONTAINER_RUNTIME','COMPOSE_RUNTIME','RUNNING_CONTAINER_COUNT','SECURITY_UPDATES_AVAILABLE','REBOOT_REQUIRED','PACKAGE_MANAGER_ERROR','ENDPOINT_AGENT_STATE')
foreach ($name in $required) {
    if (-not $values.ContainsKey($name)) { throw "Endpoint collector omitted required field: $name" }
}

$collectorInput = [ordered]@{
    asset_id = 'ZTD-ASSET-MONITORING-VM-01'
    collection_time = [DateTime]::UtcNow.ToString('o')
    source_authority = 'CODEX_EXECUTED_LIVE_RUNTIME'
    os_family = $values.OS_FAMILY
    os_release = $values.OS_RELEASE
    kernel = $values.KERNEL
    package_count = [int]$values.PACKAGE_COUNT
    container_runtime = $values.CONTAINER_RUNTIME
    compose_runtime = $values.COMPOSE_RUNTIME
    running_container_count = [int]$values.RUNNING_CONTAINER_COUNT
    security_updates_available = [int]$values.SECURITY_UPDATES_AVAILABLE
    reboot_required = [bool]::Parse($values.REBOOT_REQUIRED)
    package_manager_error = [bool]::Parse($values.PACKAGE_MANAGER_ERROR)
    endpoint_agent_state = $values.ENDPOINT_AGENT_STATE
}
$inputPath = Join-Path $outputRoot 'monitoring-vm.collector-input.json'
$normalizedPath = Join-Path $outputRoot 'monitoring-vm.evidence.json'
[IO.File]::WriteAllText($inputPath, ($collectorInput | ConvertTo-Json -Depth 5), [Text.UTF8Encoding]::new($false))

$python = (Get-Command python -ErrorAction Stop).Source
& $python (Join-Path $repoRoot 'tools\endpoint\collect_software_inventory.py') --input $inputPath --output $normalizedPath --format json
if ($LASTEXITCODE -ne 0) { throw 'Software inventory normalization failed.' }

& $python (Join-Path $repoRoot 'tools\endpoint\validate_endpoint_compliance.py') `
    --inventory (Join-Path $repoRoot 'docs\zero-trust\device\device-inventory.yaml') `
    --policy (Join-Path $repoRoot 'docs\zero-trust\device\endpoint-compliance-policy.yaml') `
    --evidence-root $outputRoot --verbose
$validationExit = $LASTEXITCODE

Write-Output "[PASS] Sanitized endpoint record: $normalizedPath"
Write-Output '[INFO] No patch, reboot, endpoint-agent installation, isolation, or exploit action was executed.'
if ($null -ne $foundationExit -and $foundationExit -ne 0) {
    Write-Output '[WARN] One or more existing infrastructure validators reported a bounded finding; see ignored runtime output.'
}
exit $validationExit
