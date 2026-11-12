#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

[[ $# -eq 2 ]] || {
  printf 'usage: %s request-snapshot|latest control-snapshot|latest\n' "$0" >&2
  exit 64
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$script_dir/../request-db/restore.sh" "$1"
"$script_dir/../control-db/restore.sh" "$2"

export PGSSLMODE="${PGSSLMODE:-verify-full}"

request_psql=(
  psql --host="$REQUEST_RESTORE_HOST" --port="${REQUEST_RESTORE_PORT:-5432}"
  --username="$REQUEST_RESTORE_USER" --dbname="$REQUEST_RESTORE_NAME"
  --tuples-only --no-align --set ON_ERROR_STOP=1
)
control_psql=(
  psql --host="$CONTROL_RESTORE_HOST" --port="${CONTROL_RESTORE_PORT:-5432}"
  --username="$CONTROL_RESTORE_USER" --dbname="$CONTROL_RESTORE_NAME"
  --tuples-only --no-align --set ON_ERROR_STOP=1
)

PGPASSFILE="$REQUEST_RESTORE_PGPASSFILE" "${request_psql[@]}" \
  --command='SELECT count(*) FROM request_service.access_requests;' >/dev/null
PGPASSFILE="$CONTROL_RESTORE_PGPASSFILE" "${control_psql[@]}" \
  --command='SELECT count(*) FROM control_service.approval_requests;' >/dev/null

while IFS='|' read -r request_id grant_status; do
  [[ -n "$request_id" ]] || continue
  case "$grant_status" in
    ACTIVE) expected_status=GRANTED ;;
    REVOKED) expected_status=REVOKED ;;
    EXPIRED) expected_status=EXPIRED ;;
    *) printf 'unexpected control grant status: %s\n' "$grant_status" >&2; exit 1 ;;
  esac
  [[ "$request_id" =~ ^[0-9A-Za-z_-]{1,64}$ ]] || { printf 'unsafe request id in restore\n' >&2; exit 1; }
  projected_status="$(PGPASSFILE="$REQUEST_RESTORE_PGPASSFILE" "${request_psql[@]}" \
    --command="SELECT status FROM request_service.access_requests WHERE request_id = '$request_id'")"
  if [[ "$projected_status" != "$expected_status" ]]; then
    printf 'projection mismatch: request=%s control=%s request-db=%s\n' \
      "$request_id" "$grant_status" "$projected_status" >&2
    exit 1
  fi
done < <(PGPASSFILE="$CONTROL_RESTORE_PGPASSFILE" "${control_psql[@]}" \
  --field-separator='|' --command='SELECT request_id, status FROM control_service.grants ORDER BY request_id')

printf 'integrated restore projection check: PASS\n'
