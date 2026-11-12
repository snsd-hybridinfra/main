#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

[[ $# -eq 1 ]] || { printf 'usage: %s request-db|control-db\n' "$0" >&2; exit 64; }
db_kind="$1"
[[ "$db_kind" == request-db || "$db_kind" == control-db ]] || exit 64

: "${RESTIC_PASSWORD_FILE:?RESTIC_PASSWORD_FILE is required}"
if [[ -z "${RESTIC_REPOSITORY:-}" ]]; then
  : "${RESTIC_REPOSITORY_FILE:?RESTIC_REPOSITORY or RESTIC_REPOSITORY_FILE is required}"
  [[ -r "$RESTIC_REPOSITORY_FILE" ]] || { printf 'RESTIC_REPOSITORY_FILE is not readable\n' >&2; exit 77; }
fi

for command_name in restic python3 sha256sum pg_restore mktemp; do
  command -v "$command_name" >/dev/null || {
    printf 'required command not found: %s\n' "$command_name" >&2
    exit 69
  }
done

verify_root="${BACKUP_VERIFY_ROOT:-/var/lib/iaas-backup/verification}"
mkdir -p "$verify_root"
target="$(mktemp -d "${verify_root%/}/${db_kind}.XXXXXXXX")"
trap 'find "$target" -type f -delete 2>/dev/null || true; find "$target" -depth -type d -empty -delete 2>/dev/null || true' EXIT

snapshot_id="$(restic snapshots --latest 1 --tag "$db_kind" --json | python3 -c 'import json,sys; data=json.load(sys.stdin); print(data[0]["short_id"] if data else "")')"
[[ -n "$snapshot_id" ]] || { printf 'no snapshot found for %s\n' "$db_kind" >&2; exit 1; }

restic restore "$snapshot_id" --target "$target"
checksum_file="$(find "$target" -type f -name SHA256SUMS -print -quit)"
[[ -n "$checksum_file" ]] || { printf 'SHA256SUMS not found\n' >&2; exit 1; }
(
  cd "$(dirname "$checksum_file")"
  sha256sum --check SHA256SUMS
  dump_file="$(find . -maxdepth 1 -type f -name '*.dump' -print -quit)"
  [[ -n "$dump_file" ]]
  pg_restore --list "$dump_file" >/dev/null
)

printf 'snapshot verification passed: db_kind=%s snapshot=%s\n' "$db_kind" "$snapshot_id"
