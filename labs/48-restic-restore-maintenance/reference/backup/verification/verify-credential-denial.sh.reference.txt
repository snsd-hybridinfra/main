#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

if [[ -z "${RESTIC_REPOSITORY:-}" ]]; then
  : "${RESTIC_REPOSITORY_FILE:?RESTIC_REPOSITORY or RESTIC_REPOSITORY_FILE is required}"
  [[ -r "$RESTIC_REPOSITORY_FILE" ]] || { printf 'RESTIC_REPOSITORY_FILE is not readable\n' >&2; exit 77; }
fi
wrong_password_file="$(mktemp)"
trap 'shred -u "$wrong_password_file" 2>/dev/null || true' EXIT
printf 'intentionally-wrong-%s\n' "$(date +%s)" > "$wrong_password_file"

if RESTIC_PASSWORD_FILE="$wrong_password_file" restic snapshots >/dev/null 2>&1; then
  printf 'repository unexpectedly accepted an invalid credential\n' >&2
  exit 1
fi

printf 'invalid restic credential denied: PASS\n'
