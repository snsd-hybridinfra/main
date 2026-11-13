#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

: "${RESTIC_PASSWORD_FILE:?RESTIC_PASSWORD_FILE is required}"
if [[ -z "${RESTIC_REPOSITORY:-}" ]]; then
  : "${RESTIC_REPOSITORY_FILE:?RESTIC_REPOSITORY or RESTIC_REPOSITORY_FILE is required}"
  [[ -r "$RESTIC_REPOSITORY_FILE" ]] || { printf 'RESTIC_REPOSITORY_FILE is not readable\n' >&2; exit 77; }
fi
export RESTIC_CACHE_DIR="${RESTIC_CACHE_DIR:-/var/cache/iaas-restic}"

restic snapshots --compact
restic check --read-data-subset="${RESTIC_CHECK_SUBSET:-5%}"
