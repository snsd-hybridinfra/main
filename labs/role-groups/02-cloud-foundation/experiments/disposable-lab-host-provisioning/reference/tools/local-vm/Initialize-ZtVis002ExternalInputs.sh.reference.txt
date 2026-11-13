#!/usr/bin/env bash
set -euo pipefail

readonly external_root="${HOME}/.config/snsd/zt-vis-002"
readonly mode="${1:-status}"

umask 077
install -d -m 0700 "${external_root}"

cleanup_staging() {
  local staging="${1:-}"
  case "${staging}" in
    "${external_root}"/.material-staging.*|"${external_root}"/.incoming.*)
      rm -rf -- "${staging}"
      ;;
    *)
      printf 'refusing unsafe cleanup path\n' >&2
      return 1
      ;;
  esac
}

verify_materials() {
  test -s "${external_root}/pki/ca.crt"
  test -s "${external_root}/pki/ca.key"
  test -s "${external_root}/pki/server.crt"
  test -s "${external_root}/pki/server.key"
  test -s "${external_root}/pki/client.crt"
  test -s "${external_root}/pki/client.key"
  test -s "${external_root}/secrets/grafana_admin_password"
  openssl verify \
    -CAfile "${external_root}/pki/ca.crt" \
    "${external_root}/pki/server.crt" \
    "${external_root}/pki/client.crt" >/dev/null
  openssl x509 -in "${external_root}/pki/server.crt" -noout -checkhost zt-vis-002-monitoring.lab.internal >/dev/null
  test "$(stat -c '%a' "${external_root}")" = "700"
  test "$(stat -c '%a' "${external_root}/pki/ca.key")" = "600"
  test "$(stat -c '%a' "${external_root}/pki/server.key")" = "600"
  test "$(stat -c '%a' "${external_root}/pki/client.key")" = "600"
  test "$(stat -c '%a' "${external_root}/secrets/grafana_admin_password")" = "600"
}

initialize_materials() {
  if test -e "${external_root}/pki" || test -e "${external_root}/secrets"; then
    verify_materials
    printf 'materials=PRESENT_VERIFIED\n'
    return
  fi

  local staging
  staging="$(mktemp -d "${external_root}/.material-staging.XXXXXX")"
  trap 'cleanup_staging "${staging}"' EXIT
  install -d -m 0700 "${staging}/pki" "${staging}/secrets"

  openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:3072 \
    -out "${staging}/pki/ca.key" 2>/dev/null
  openssl req -x509 -new -sha256 -days 365 \
    -key "${staging}/pki/ca.key" \
    -out "${staging}/pki/ca.crt" \
    -subj '/CN=SNSD ZT-VIS-002 Lab CA/O=SNSD Lab' \
    -addext 'basicConstraints=critical,CA:TRUE' \
    -addext 'keyUsage=critical,keyCertSign,cRLSign' 2>/dev/null

  openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:3072 \
    -out "${staging}/pki/server.key" 2>/dev/null
  openssl req -new -sha256 \
    -key "${staging}/pki/server.key" \
    -out "${staging}/pki/server.csr" \
    -subj '/CN=zt-vis-002-monitoring.lab.internal/O=SNSD Lab' 2>/dev/null
  printf '%s\n' \
    'subjectAltName=DNS:zt-vis-002-monitoring.lab.internal' \
    'extendedKeyUsage=serverAuth' \
    'keyUsage=critical,digitalSignature,keyEncipherment' \
    > "${staging}/pki/server.ext"
  openssl x509 -req -sha256 -days 365 \
    -in "${staging}/pki/server.csr" \
    -CA "${staging}/pki/ca.crt" \
    -CAkey "${staging}/pki/ca.key" \
    -CAcreateserial \
    -out "${staging}/pki/server.crt" \
    -extfile "${staging}/pki/server.ext" 2>/dev/null

  openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:3072 \
    -out "${staging}/pki/client.key" 2>/dev/null
  openssl req -new -sha256 \
    -key "${staging}/pki/client.key" \
    -out "${staging}/pki/client.csr" \
    -subj '/CN=visibility-operator/O=SNSD Lab' 2>/dev/null
  printf '%s\n' \
    'extendedKeyUsage=clientAuth' \
    'keyUsage=critical,digitalSignature' \
    > "${staging}/pki/client.ext"
  openssl x509 -req -sha256 -days 365 \
    -in "${staging}/pki/client.csr" \
    -CA "${staging}/pki/ca.crt" \
    -CAkey "${staging}/pki/ca.key" \
    -CAserial "${staging}/pki/ca.srl" \
    -out "${staging}/pki/client.crt" \
    -extfile "${staging}/pki/client.ext" 2>/dev/null

  openssl rand -base64 48 > "${staging}/secrets/grafana_admin_password"
  (
    cd "${staging}/pki"
    sha256sum ca.crt server.crt client.crt > certificate-sha256.txt
  )
  find "${staging}" -type f -exec chmod 0600 {} +
  openssl verify \
    -CAfile "${staging}/pki/ca.crt" \
    "${staging}/pki/server.crt" \
    "${staging}/pki/client.crt" >/dev/null
  openssl x509 -in "${staging}/pki/server.crt" -noout -checkhost zt-vis-002-monitoring.lab.internal >/dev/null

  mv "${staging}/pki" "${external_root}/pki"
  mv "${staging}/secrets" "${external_root}/secrets"
  trap - EXIT
  rmdir "${staging}"
  verify_materials
  printf 'materials=CREATED_VERIFIED\n'
}

install_stream() {
  local destination="$1"
  local required_pattern="$2"
  local forbidden_pattern="$3"
  local staging
  staging="$(mktemp -d "${external_root}/.incoming.XXXXXX")"
  trap 'cleanup_staging "${staging}"' EXIT
  cat > "${staging}/payload"
  test -s "${staging}/payload"
  grep -Eq "${required_pattern}" "${staging}/payload"
  if grep -Eiq "${forbidden_pattern}" "${staging}/payload"; then
    printf 'external input contains a forbidden placeholder or secret field\n' >&2
    return 1
  fi
  chmod 0600 "${staging}/payload"
  mv "${staging}/payload" "${external_root}/${destination}"
  trap - EXIT
  rmdir "${staging}"
  printf '%s=INSTALLED_STRUCTURALLY_VALIDATED\n' "${destination}"
}

status() {
  if verify_materials 2>/dev/null; then
    printf 'materials=READY\n'
  else
    printf 'materials=NOT_READY\n'
  fi
  for file in clouds.yaml terraform.tfvars; do
    if test -s "${external_root}/${file}" && test "$(stat -c '%a' "${external_root}/${file}")" = "600"; then
      printf '%s=READY\n' "${file}"
    else
      printf '%s=NOT_READY\n' "${file}"
    fi
  done
}

case "${mode}" in
  init-materials)
    initialize_materials
    ;;
  install-cloud-profile)
    install_stream 'clouds.yaml' '^clouds:' '(^|[[:space:]])(<[^>]+>|CHANGE_ME|REPLACE_ME)([[:space:]]|$)'
    ;;
  install-tfvars)
    install_stream 'terraform.tfvars' '^openstack_cloud[[:space:]]*=' '(<[^>]+>|CHANGE_ME|REPLACE_ME|password[[:space:]]*=|token[[:space:]]*=|secret[[:space:]]*=)'
    ;;
  status)
    status
    ;;
  *)
    printf 'usage: %s {init-materials|install-cloud-profile|install-tfvars|status}\n' "$0" >&2
    exit 2
    ;;
esac
