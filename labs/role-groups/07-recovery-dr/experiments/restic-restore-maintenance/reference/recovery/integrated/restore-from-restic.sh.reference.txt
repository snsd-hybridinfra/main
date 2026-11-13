#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

[[ $# -eq 2 ]] || {
  printf 'usage: %s request-db|control-db|identity-db snapshot-id|latest\n' "$0" >&2
  exit 64
}
db_kind="$1"
snapshot_selector="$2"
[[ "$db_kind" == request-db || "$db_kind" == control-db || "$db_kind" == identity-db ]] || exit 64

: "${RESTIC_PASSWORD_FILE:?RESTIC_PASSWORD_FILE is required}"
if [[ -z "${RESTIC_REPOSITORY:-}" ]]; then
  : "${RESTIC_REPOSITORY_FILE:?RESTIC_REPOSITORY or RESTIC_REPOSITORY_FILE is required}"
  [[ -r "$RESTIC_REPOSITORY_FILE" ]] || { printf 'RESTIC_REPOSITORY_FILE is not readable\n' >&2; exit 77; }
fi
: "${RESTORE_DB_HOST:?RESTORE_DB_HOST is required}"
: "${RESTORE_DB_NAME:?RESTORE_DB_NAME is required}"
: "${RESTORE_DB_USER:?RESTORE_DB_USER is required}"
: "${PGPASSFILE:?PGPASSFILE is required}"
: "${PGSSLROOTCERT:?PGSSLROOTCERT is required}"

restore_db_port="${RESTORE_DB_PORT:-5432}"
restore_root="${RECOVERY_STAGING_ROOT:-/var/lib/iaas-recovery/staging}"

[[ "$RESTORE_DB_NAME" =~ ^[A-Za-z0-9_]+_restore(_[A-Za-z0-9_]+)?$ ]] || {
  printf 'refusing non-isolated target database name: %s (must end in _restore)\n' "$RESTORE_DB_NAME" >&2
  exit 78
}

for command_name in restic pg_restore psql createdb dropdb sha256sum python3; do
  command -v "$command_name" >/dev/null || { printf 'missing command: %s\n' "$command_name" >&2; exit 69; }
done

mkdir -p "$restore_root"
work_dir="$(mktemp -d "${restore_root%/}/${db_kind}.XXXXXXXX")"
created_database=false
cleanup() {
  result=$?
  if [[ $result -ne 0 && "$created_database" == true ]]; then
    dropdb --if-exists \
      --host="$RESTORE_DB_HOST" --port="$restore_db_port" --username="$RESTORE_DB_USER" \
      "$RESTORE_DB_NAME" || true
  fi
  find "$work_dir" -type f -exec shred -u {} + 2>/dev/null || true
  find "$work_dir" -depth -type d -empty -delete 2>/dev/null || true
  exit "$result"
}
trap cleanup EXIT INT TERM

export PGSSLMODE="${PGSSLMODE:-verify-full}"

if [[ "$snapshot_selector" == latest ]]; then
  snapshot_id="$(restic snapshots --latest 1 --tag "$db_kind" --json | python3 -c 'import json,sys; data=json.load(sys.stdin); print(data[0]["short_id"] if data else "")')"
else
  [[ "$snapshot_selector" =~ ^[0-9a-fA-F]{8,64}$ ]] || { printf 'invalid snapshot id\n' >&2; exit 64; }
  snapshot_id="$snapshot_selector"
fi
[[ -n "$snapshot_id" ]] || { printf 'snapshot not found for %s\n' "$db_kind" >&2; exit 1; }

restic restore "$snapshot_id" --target "$work_dir"
checksum_file="$(find "$work_dir" -type f -name SHA256SUMS -print -quit)"
metadata_file="$(find "$work_dir" -type f -name METADATA -print -quit)"
[[ -n "$checksum_file" && -n "$metadata_file" ]] || { printf 'backup manifest is incomplete\n' >&2; exit 1; }
grep -Fxq "db_kind=$db_kind" "$metadata_file" || { printf 'snapshot DB kind mismatch\n' >&2; exit 1; }

dump_dir="$(dirname "$checksum_file")"
(
  cd "$dump_dir"
  sha256sum --check SHA256SUMS
)
dump_file="$(find "$dump_dir" -maxdepth 1 -type f -name '*.dump' -print -quit)"
[[ -n "$dump_file" ]] || { printf 'dump file not found\n' >&2; exit 1; }
pg_restore --list "$dump_file" >/dev/null

database_exists="$(psql \
  --host="$RESTORE_DB_HOST" --port="$restore_db_port" --username="$RESTORE_DB_USER" \
  --dbname=postgres --tuples-only --no-align \
  --command="SELECT 1 FROM pg_database WHERE datname = '$RESTORE_DB_NAME'")"
[[ -z "$database_exists" ]] || { printf 'isolated target already exists: %s\n' "$RESTORE_DB_NAME" >&2; exit 73; }

createdb \
  --host="$RESTORE_DB_HOST" --port="$restore_db_port" --username="$RESTORE_DB_USER" \
  --template=template0 --encoding=UTF8 "$RESTORE_DB_NAME"
created_database=true

pg_restore \
  --host="$RESTORE_DB_HOST" --port="$restore_db_port" --username="$RESTORE_DB_USER" \
  --dbname="$RESTORE_DB_NAME" \
  --no-owner --no-privileges --exit-on-error --single-transaction \
  "$dump_file"

if [[ "$db_kind" == request-db ]]; then
  schema_name=request_service
  required_table=access_requests
elif [[ "$db_kind" == control-db ]]; then
  schema_name=control_service
  required_table=audit_events
else
  schema_name=keycloak
  required_table=realm
fi

psql \
  --host="$RESTORE_DB_HOST" --port="$restore_db_port" --username="$RESTORE_DB_USER" \
  --dbname="$RESTORE_DB_NAME" --set ON_ERROR_STOP=1 \
  --command="SELECT count(*) AS restored_rows FROM ${schema_name}.${required_table};" \
  --command="ANALYZE ${schema_name}.${required_table};"

created_database=false
printf 'isolated restore completed: db_kind=%s snapshot=%s target=%s\n' \
  "$db_kind" "$snapshot_id" "$RESTORE_DB_NAME"
