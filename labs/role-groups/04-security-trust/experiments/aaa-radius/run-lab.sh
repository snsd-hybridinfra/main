#!/usr/bin/env bash
set -euo pipefail

image='freeradius/freeradius-server@sha256:91acbee4a1f532e3a266ae3d7f153a5cf21f5faa9bc14116d5d1fe2c2a746c27'
tmp=$(mktemp -d /tmp/lab06-radius-XXXXXXXX)
container_id=''
cleanup() {
  if [ -n "$container_id" ]; then docker rm -f "$container_id" >/dev/null 2>&1 || true; fi
  case "$tmp" in /tmp/lab06-radius-*) rm -rf -- "$tmp" ;; esac
}
trap cleanup EXIT

secret=$(openssl rand -hex 24)
password=$(openssl rand -hex 24)
wrong=$(openssl rand -hex 24)
cat > "$tmp/clients.conf" <<EOF
client loopback-lab {
    ipaddr = 127.0.0.1
    secret = $secret
}
EOF
cat > "$tmp/authorize" <<EOF
lab-admin Cleartext-Password := "$password"
    Service-Type = Administrative-User
EOF
container_id=$(docker run -d --network none \
  -v "$tmp/clients.conf:/etc/raddb/clients.conf:ro" \
  -v "$tmp/authorize:/etc/raddb/mods-config/files/authorize:ro" \
  "$image")
sleep 1
if [ "$(docker inspect -f '{{.State.Running}}' "$container_id")" != "true" ]; then
  echo 'RADIUS server failed to start' >&2
  exit 1
fi

run_case() {
  local label="$1" user="$2" pass="$3" expected="$4"
  local result
  result=$(docker exec "$container_id" /opt/bin/radtest "$user" "$pass" 127.0.0.1 0 "$secret" 0 127.0.0.1 2>&1) || true
  if ! grep -q "Received Access-$expected" <<< "$result"; then
    echo "$label: FAIL (expected Access-$expected)" >&2
    sed -e "s/$password/[redacted]/g" -e "s/$secret/[redacted]/g" -e "s/$wrong/[redacted]/g" <<< "$result" | head -15 >&2
    exit 1
  fi
  echo "$label: Access-$expected"
}
run_case approved_user lab-admin "$password" Accept
run_case wrong_password lab-admin "$wrong" Reject
run_case unknown_user lab-unknown "$password" Reject
echo 'server_network: none (loopback only)'
echo 'test_secret_and_password: generated at runtime; omitted'
