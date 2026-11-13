#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

: "${RESTIC_PASSWORD_FILE:?RESTIC_PASSWORD_FILE is required}"
if [[ -z "${RESTIC_REPOSITORY:-}" ]]; then
  : "${RESTIC_REPOSITORY_FILE:?RESTIC_REPOSITORY or RESTIC_REPOSITORY_FILE is required}"
  [[ -r "$RESTIC_REPOSITORY_FILE" ]] || { printf 'RESTIC_REPOSITORY_FILE is not readable\n' >&2; exit 77; }
fi
[[ "${RESTIC_MAINTENANCE_MODE:-}" == "full-access-approved" ]] || {
  printf 'RESTIC_MAINTENANCE_MODE=full-access-approved is required\n' >&2
  exit 78
}

for command_name in restic flock; do
  command -v "$command_name" >/dev/null || {
    printf 'required command not found: %s\n' "$command_name" >&2
    exit 69
  }
done

[[ -r "$RESTIC_PASSWORD_FILE" ]] || {
  printf 'RESTIC_PASSWORD_FILE is not readable\n' >&2
  exit 77
}

export RESTIC_CACHE_DIR="${RESTIC_CACHE_DIR:-/var/cache/iaas-restic}"
mkdir -p "$RESTIC_CACHE_DIR"

staging_root="${BACKUP_STAGING_ROOT:-/var/lib/iaas-backup/staging}"
mkdir -p "$staging_root"
exec 9>"${staging_root%/}/restic-operation.lock"
flock -w "${RESTIC_LOCK_WAIT_SECONDS:-1800}" 9 || {
  printf 'timed out waiting for the Restic operation lock\n' >&2
  exit 75
}

for db_kind in request-db control-db; do
  restic forget \
    --host "${BACKUP_HOST_ID:-iaas-backup-worker}" \
    --tag "$db_kind" \
    --group-by host,tags \
    --keep-within-daily "${RESTIC_KEEP_WITHIN_DAILY:-7d}" \
    --keep-within-weekly "${RESTIC_KEEP_WITHIN_WEEKLY:-1m}" \
    --keep-within-monthly "${RESTIC_KEEP_WITHIN_MONTHLY:-6m}"
done

restic forget \
  --host "${BACKUP_HOST_ID:-iaas-backup-worker}" \
  --tag append-only-canary \
  --group-by host,tags \
  --keep-last 1

restic prune
restic check --read-data-subset="${RESTIC_CHECK_SUBSET:-5%}"

printf 'Restic retention, prune, and repository check completed\n'
