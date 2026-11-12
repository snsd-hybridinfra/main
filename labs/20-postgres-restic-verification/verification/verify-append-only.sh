#!/usr/bin/env bash
set -Eeuo pipefail
if [[ "${LAB_ALLOW_RESTIC_CANARY:-}" != "YES" ]]; then
  printf 'Append-only canary test blocked. Use only a disposable test repository and set LAB_ALLOW_RESTIC_CANARY=YES.\n' >&2
  exit 78
fi
umask 077

: "${RESTIC_PASSWORD_FILE:?RESTIC_PASSWORD_FILE is required}"
if [[ -z "${RESTIC_REPOSITORY:-}" ]]; then
  : "${RESTIC_REPOSITORY_FILE:?RESTIC_REPOSITORY or RESTIC_REPOSITORY_FILE is required}"
  [[ -r "$RESTIC_REPOSITORY_FILE" ]] || { printf 'RESTIC_REPOSITORY_FILE is not readable\n' >&2; exit 77; }
fi

for command_name in restic python3 mktemp grep flock; do
  command -v "$command_name" >/dev/null || {
    printf 'required command not found: %s\n' "$command_name" >&2
    exit 69
  }
done

canary_root="${BACKUP_VERIFY_ROOT:-/var/lib/iaas-backup/verification}"
mkdir -p "$canary_root"
staging_root="${BACKUP_STAGING_ROOT:-/var/lib/iaas-backup/staging}"
mkdir -p "$staging_root"
exec 9>"${staging_root%/}/restic-operation.lock"
flock -w "${RESTIC_LOCK_WAIT_SECONDS:-1800}" 9 || {
  printf 'timed out waiting for the Restic operation lock\n' >&2
  exit 75
}
canary_dir="$(mktemp -d "${canary_root%/}/append-only.XXXXXXXX")"
trap 'find "$canary_dir" -type f -delete 2>/dev/null || true; rmdir "$canary_dir" 2>/dev/null || true' EXIT
printf 'append-only authorization canary: %s\n' "$(date -u +%Y%m%dT%H%M%SZ)" > "$canary_dir/CANARY"

restic backup "$canary_dir" \
  --host "${BACKUP_HOST_ID:-iaas-backup-worker}" \
  --tag credential-control \
  --tag append-only-canary

snapshot_id="$(restic snapshots \
  --host "${BACKUP_HOST_ID:-iaas-backup-worker}" \
  --tag append-only-canary --latest 1 --json |
  python3 -c 'import json,sys; data=json.load(sys.stdin); print(data[0]["short_id"] if data else "")')"
[[ -n "$snapshot_id" ]] || { printf 'canary snapshot was not created\n' >&2; exit 1; }

set +e
deny_output="$(restic forget "$snapshot_id" 2>&1)"
deny_status=$?
set -e

if [[ $deny_status -eq 0 ]]; then
  printf 'append-only check failed: backup credential deleted its canary snapshot\n' >&2
  exit 1
fi
if ! printf '%s' "$deny_output" | grep -Eqi '403|forbidden|denied|not allowed|append.?only'; then
  printf 'append-only check inconclusive; forget failed without an authorization denial\n' >&2
  exit 1
fi

printf 'append-only delete denial: PASS snapshot=%s\n' "$snapshot_id"
