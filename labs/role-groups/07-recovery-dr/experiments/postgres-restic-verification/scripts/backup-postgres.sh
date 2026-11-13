#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

usage() {
  printf 'usage: %s request-db|control-db|identity-db\n' "$0" >&2
  exit 64
}

[[ $# -eq 1 ]] || usage
db_kind="$1"

case "$db_kind" in
  request-db)
    db_host="${REQUEST_DB_HOST:?REQUEST_DB_HOST is required}"
    db_port="${REQUEST_DB_PORT:-5432}"
    db_name="${REQUEST_DB_NAME:-request_db}"
    db_user="${REQUEST_DB_USER:-request_backup}"
    db_schema="request_service"
    ;;
  control-db)
    db_host="${CONTROL_DB_HOST:?CONTROL_DB_HOST is required}"
    db_port="${CONTROL_DB_PORT:-5432}"
    db_name="${CONTROL_DB_NAME:-control_db}"
    db_user="${CONTROL_DB_USER:-control_backup}"
    db_schema="control_service"
    ;;
  identity-db)
    db_host="${IDENTITY_DB_HOST:?IDENTITY_DB_HOST is required}"
    db_port="${IDENTITY_DB_PORT:-5432}"
    db_name="${IDENTITY_DB_NAME:-identity_db}"
    db_user="${IDENTITY_DB_USER:-identity_backup}"
    db_schema="keycloak"
    ;;
  *) usage ;;
esac

: "${PGPASSFILE:?PGPASSFILE must point to a mode-0600 credential file}"
: "${RESTIC_PASSWORD_FILE:?RESTIC_PASSWORD_FILE is required}"
if [[ -z "${RESTIC_REPOSITORY:-}" ]]; then
  : "${RESTIC_REPOSITORY_FILE:?RESTIC_REPOSITORY or RESTIC_REPOSITORY_FILE is required}"
  [[ -r "$RESTIC_REPOSITORY_FILE" ]] || { printf 'RESTIC_REPOSITORY_FILE is not readable\n' >&2; exit 77; }
fi

for command_name in pg_dump pg_restore restic sha256sum mktemp flock; do
  command -v "$command_name" >/dev/null || {
    printf 'required command not found: %s\n' "$command_name" >&2
    exit 69
  }
done

[[ -r "$PGPASSFILE" ]] || { printf 'PGPASSFILE is not readable\n' >&2; exit 77; }
[[ -r "$RESTIC_PASSWORD_FILE" ]] || { printf 'RESTIC_PASSWORD_FILE is not readable\n' >&2; exit 77; }

staging_root="${BACKUP_STAGING_ROOT:-/var/lib/iaas-backup/staging}"
mkdir -p "$staging_root"
work_dir="$(mktemp -d "${staging_root%/}/${db_kind}.XXXXXXXX")"
cleanup() {
  find "$work_dir" -type f -exec shred -u {} + 2>/dev/null || true
  rmdir "$work_dir" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
dump_name="${db_kind}-${timestamp}.dump"

export PGSSLMODE="${PGSSLMODE:-verify-full}"
export PGSSLROOTCERT="${PGSSLROOTCERT:?PGSSLROOTCERT is required}"
export RESTIC_CACHE_DIR="${RESTIC_CACHE_DIR:-/var/cache/iaas-restic}"
mkdir -p "$RESTIC_CACHE_DIR"

pg_dump \
  --host="$db_host" \
  --port="$db_port" \
  --username="$db_user" \
  --dbname="$db_name" \
  --schema="$db_schema" \
  --format=custom \
  --compress=zstd:6 \
  --no-owner \
  --no-privileges \
  --serializable-deferrable \
  --file="$work_dir/$dump_name"

pg_restore --list "$work_dir/$dump_name" >/dev/null
(
  cd "$work_dir"
  sha256sum "$dump_name" > SHA256SUMS
  printf 'db_kind=%s\ndatabase=%s\nschema=%s\ncreated_at=%s\n' \
    "$db_kind" "$db_name" "$db_schema" "$timestamp" > METADATA
)

restic_lock="${BACKUP_STAGING_ROOT:-/var/lib/iaas-backup/staging}/restic-operation.lock"
exec 9>"$restic_lock"
flock -w "${RESTIC_LOCK_WAIT_SECONDS:-1800}" 9 || {
  printf 'timed out waiting for the Restic operation lock\n' >&2
  exit 75
}

restic backup "$work_dir" \
  --host "${BACKUP_HOST_ID:-iaas-backup-worker}" \
  --tag postgres \
  --tag "$db_kind" \
  --tag logical-dump

printf 'backup completed: db_kind=%s created_at=%s\n' "$db_kind" "$timestamp"
