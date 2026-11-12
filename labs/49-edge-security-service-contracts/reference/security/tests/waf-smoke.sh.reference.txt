#!/usr/bin/env bash
set -Eeuo pipefail

base_url="${EDGE_BASE_URL:-https://user.example.com}"
admin_url="${ADMIN_BASE_URL:-https://admin.example.com}"
curl_args=(--silent --show-error --output /dev/null --connect-timeout 5 --max-time 15)

if [[ "${EDGE_INSECURE_TEST_ONLY:-false}" == "true" ]]; then
  curl_args+=(--insecure)
fi

expect_status() {
  local expected="$1"
  local label="$2"
  shift 2
  local actual
  actual="$(curl "${curl_args[@]}" --write-out '%{http_code}' "$@")"
  if [[ "$actual" != "$expected" ]]; then
    printf '%s: expected HTTP %s, got %s\n' "$label" "$expected" "$actual" >&2
    return 1
  fi
  printf '%s: HTTP %s\n' "$label" "$actual"
}

expect_status 200 health "$base_url/healthz"
expect_status 403 sqli "$base_url/api/v1/requests?filter=1%27%20OR%201%3D1--"
expect_status 403 xss \
  --request POST \
  --header 'Content-Type: application/json' \
  --data '{"product_code":"DEV-OS-VM-S","cpu":0,"memory_gib":0,"storage_gib":0,"duration_hours":24,"purpose":"<script>alert(1)</script>","parameters":{"project_name":"waf-smoke-test","workload_purpose":"security-validation"}}' \
  "$base_url/api/v1/requests"
expect_status 403 admin-sqli "$admin_url/admin-api/v1/requests?status=PENDING%27%20OR%20%271%27%3D%271"
