[CmdletBinding()]
param(
    [ValidateSet('Check', 'Deploy', 'Validate', 'Persistence')]
    [string]$Mode = 'Check'
)

$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$sourceRoot = Join-Path $repoRoot 'observability\logging'
$runtimeRoot = Join-Path $repoRoot '.runtime\zero-trust\persistent-telemetry'
$keyPath = Join-Path $HOME '.ssh\codex_monitoring_operator_ed25519'
$knownHosts = Join-Path $HOME '.ssh\known_hosts_snsd_monitoring'
$openStack = 'sudo -n env OS_CLIENT_CONFIG_FILE=/etc/kolla/clouds.yaml /opt/openstack-client/bin/openstack --os-cloud kolla-admin'
$portName = 'snsd-monitoring-01-port'

$requiredFiles = @(
    'compose.yaml',
    'loki-config.yaml',
    'alloy-config.alloy',
    'grafana-provisioning\datasources\loki.yaml'
)

foreach ($relativePath in $requiredFiles) {
    $path = Join-Path $sourceRoot $relativePath
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Required telemetry configuration is missing: $relativePath"
    }
}

foreach ($path in @($keyPath, $knownHosts)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Required monitoring access file is missing: $path"
    }
}

$fixedIps = (& ssh -o BatchMode=yes openstack-operator "$openStack port show $portName -f value -c fixed_ips").Trim()
if ($LASTEXITCODE -ne 0) { throw 'Unable to resolve the monitoring VM address.' }
$vmIp = [regex]::Match($fixedIps, '(?<![0-9])(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?![0-9])').Value

$networkId = (& ssh -o BatchMode=yes openstack-operator "$openStack port show $portName -f value -c network_id").Trim()
if ($LASTEXITCODE -ne 0 -or -not $vmIp -or -not $networkId) {
    throw 'Unable to resolve the monitoring VM target scope.'
}

$namespace = "qdhcp-$networkId"
$proxyCommand = "ssh -o BatchMode=yes openstack-operator sudo -n ip netns exec $namespace /usr/bin/nc %h %p"
$sshArgs = @(
    '-o', 'BatchMode=yes',
    '-o', 'ConnectTimeout=10',
    '-o', 'IdentitiesOnly=yes',
    '-i', $keyPath,
    '-o', 'StrictHostKeyChecking=yes',
    '-o', "UserKnownHostsFile=$knownHosts",
    '-o', "ProxyCommand=$proxyCommand",
    "ubuntu@$vmIp"
)

function Invoke-MonitoringCommand {
    param([Parameter(Mandatory)][string]$Command)
    & ssh @sshArgs $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Monitoring command failed with exit code $LASTEXITCODE."
    }
}

function Invoke-EncodedMonitoringScript {
    param([Parameter(Mandatory)][string]$Script)
    $encoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($Script))
    Invoke-MonitoringCommand -Command "printf '%s' '$encoded' | base64 -d | sudo -n bash -s"
}

New-Item -ItemType Directory -Path $runtimeRoot -Force | Out-Null

if ($Mode -eq 'Check') {
    Invoke-MonitoringCommand -Command "hostname; sudo -n true; docker --version; docker compose version; test -d /opt/snsd-monitoring || true"
    Write-Output '[PASS] Monitoring VM access and Docker prerequisites are available.'
    Write-Output '[PASS] Repository telemetry configuration is complete.'
    exit 0
}

if ($Mode -eq 'Deploy') {
    $stageName = 'snsd-monitoring-config-' + [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')
    $remoteStage = "/tmp/$stageName"
    & ssh @sshArgs "mkdir -m 0700 $remoteStage"
    if ($LASTEXITCODE -ne 0) { throw 'Unable to create the remote staging directory.' }

    $scpArgs = @(
        '-o', 'BatchMode=yes',
        '-o', 'ConnectTimeout=10',
        '-o', 'IdentitiesOnly=yes',
        '-i', $keyPath,
        '-o', 'StrictHostKeyChecking=yes',
        '-o', "UserKnownHostsFile=$knownHosts",
        '-o', "ProxyCommand=$proxyCommand",
        '-r',
        "$sourceRoot\*",
        "ubuntu@${vmIp}:$remoteStage/"
    )
    & scp @scpArgs
    if ($LASTEXITCODE -ne 0) { throw 'Unable to stage the telemetry configuration.' }

    $deployScript = @"
set -Eeuo pipefail
stage='$remoteStage'
base=/opt/snsd-monitoring
config="`$base/config"
backup="`$base/backups/`$(date -u +%Y%m%dT%H%M%SZ)"

install -d -m 0750 "`$base" "`$base/backups" "`$base/secrets" "`$base/input/sanitized"
install -d -m 0750 "`$base/data" "`$base/data/loki" "`$base/data/grafana" "`$base/data/alloy"

if [ -d "`$config" ]; then
  install -d -m 0750 "`$backup"
  cp -a "`$config/." "`$backup/"
fi

rm -rf "`$config.new"
install -d -m 0750 "`$config.new"
cp -a "`$stage/." "`$config.new/"
docker compose -f "`$config.new/compose.yaml" config --quiet

if [ ! -s "`$base/secrets/grafana_admin_password" ]; then
  umask 077
  openssl rand -base64 32 | tr -d '\n' > "`$base/secrets/grafana_admin_password"
fi
chmod 0600 "`$base/secrets/grafana_admin_password"
chown root:root "`$base/secrets/grafana_admin_password"
chown -R 10001:10001 "`$base/data/loki"
chown -R 472:472 "`$base/data/grafana"
chown -R root:root "`$base/data/alloy" "`$base/input/sanitized"
chmod 0750 "`$base/data/alloy" "`$base/input/sanitized"

if [ -d "`$config" ]; then
  rm -rf "`$config.previous"
  mv "`$config" "`$config.previous"
fi
mv "`$config.new" "`$config"

cd "`$config"
for image in `$(docker compose config --images | sort -u); do
  if docker image inspect "`$image" >/dev/null 2>&1; then
    echo "PINNED_IMAGE_CACHE=PASS IMAGE=`$image"
    continue
  fi
  pull_ok=0
  for pull_attempt in 1 2 3 4 5; do
    if docker pull "`$image"; then
      pull_ok=1
      break
    fi
    echo "IMAGE_PULL_RETRY=`$pull_attempt IMAGE=`$image"
    sleep 10
  done
  if [ "`$pull_ok" -ne 1 ]; then
    echo "PINNED_IMAGE_PULL=FAIL IMAGE=`$image"
    exit 1
  fi
done
echo 'PINNED_IMAGE_PULL=PASS'
docker compose up -d --pull never
rm -rf "`$stage"

echo 'PERSISTENT_TELEMETRY_DEPLOY=PASS'
"@
    Invoke-EncodedMonitoringScript -Script $deployScript
    Write-Output '[PASS] Pinned persistent telemetry stack deployment completed.'
    exit 0
}

if ($Mode -eq 'Persistence') {
    $persistenceScript = @'
set -Eeuo pipefail
base=/opt/snsd-monitoring
config="$base/config"
cd "$config"

query_event() {
  curl -fsSG http://127.0.0.1:3100/loki/api/v1/query_range \
    --data-urlencode 'query={job="snsd-sanitized-validation"}' \
    --data-urlencode 'limit=20' | grep -Fq 'VISIBILITY_STACK_VALIDATION'
}

query_event
echo 'PRE_RESTART_QUERY=PASS'
docker compose restart

for attempt in $(seq 1 24); do
  healthy=1
  for service in loki alloy grafana; do
    container_id="$(docker compose ps -q "$service")"
    state="$(docker inspect -f '{{.State.Status}}' "$container_id")"
    health="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$container_id")"
    if [ "$state" != running ] || [ "$health" != healthy ]; then
      healthy=0
    fi
  done
  if [ "$healthy" -eq 1 ] \
      && curl -fsS http://127.0.0.1:3100/ready >/dev/null \
      && curl -fsS http://127.0.0.1:12345/-/ready >/dev/null \
      && curl -fsS http://127.0.0.1:3000/api/health >/dev/null; then
    break
  fi
  sleep 5
done

if [ "$healthy" -ne 1 ]; then
  echo 'POST_RESTART_HEALTH=FAIL'
  exit 1
fi
echo 'POST_RESTART_HEALTH=PASS'
query_event
echo 'POST_RESTART_QUERY=PASS'
echo 'PERSISTENT_TELEMETRY_RESTART_VALIDATE=PASS'
'@
    Invoke-EncodedMonitoringScript -Script $persistenceScript
    Write-Output '[PASS] Persistent telemetry restart validation completed.'
    exit 0
}

$validateScript = @'
set -Eeuo pipefail
base=/opt/snsd-monitoring
config="$base/config"
cd "$config"

docker compose config --quiet
for service in loki alloy grafana; do
  container_id="$(docker compose ps -q "$service")"
  test -n "$container_id"
  state="$(docker inspect -f '{{.State.Status}}' "$container_id")"
  health="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$container_id")"
  if [ "$state" != running ] || [ "$health" != healthy ]; then
    echo "SERVICE_${service}=FAIL"
    docker compose ps
    exit 1
  fi
  echo "SERVICE_${service}=PASS"
done

curl -fsS http://127.0.0.1:3100/ready >/dev/null
curl -fsS http://127.0.0.1:12345/-/ready >/dev/null
curl -fsS http://127.0.0.1:3000/api/health >/dev/null
echo 'ENDPOINT_HEALTH=PASS'

test -d "$base/data/loki"
test -d "$base/data/grafana"
test -d "$base/data/alloy"
grep -Eq '^  retention_period: 336h$' "$config/loki-config.yaml"
echo 'PERSISTENCE_RETENTION=PASS'

marker="VISIBILITY_STACK_VALIDATION_$(date -u +%Y%m%dT%H%M%SZ)_$$"
event_file="$base/input/sanitized/zt-vis-001-runtime-validation-${marker}.jsonl"
printf '{"schema_version":"1.0","event_type":"VISIBILITY_STACK_VALIDATION","event_id":"%s","environment":"disposable-lab","outcome":"PASS","sensitivity":"SANITIZED"}\n' "$marker" > "$event_file"
chmod 0640 "$event_file"

ingested=0
for attempt in $(seq 1 12); do
  if curl -fsSG http://127.0.0.1:3100/loki/api/v1/query_range \
      --data-urlencode 'query={job="snsd-sanitized-validation"}' \
      --data-urlencode 'limit=100' | grep -Fq "$marker"; then
    ingested=1
    break
  fi
  sleep 5
done
if [ "$ingested" -ne 1 ]; then
  echo 'SANITIZED_INGESTION=FAIL'
  exit 1
fi
echo 'SANITIZED_INGESTION=PASS'

if grep -R -E -i '(BEGIN [A-Z ]*PRIVATE KEY|password[[:space:]]*[:=][[:space:]]*[^<]|gh[pousr]_[A-Za-z0-9]{20,})' "$base/input/sanitized"; then
  echo 'SANITIZED_INPUT_SCAN=FAIL'
  exit 1
fi
echo 'SANITIZED_INPUT_SCAN=PASS'
rm -f "$event_file"
echo 'PERSISTENT_TELEMETRY_VALIDATE=PASS'
'@
Invoke-EncodedMonitoringScript -Script $validateScript
Write-Output '[PASS] Persistent telemetry runtime validation completed.'
