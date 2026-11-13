#!/usr/bin/env bash
set -Eeuo pipefail

[[ $# -eq 1 ]] || { printf 'usage: %s snapshot-id|latest\n' "$0" >&2; exit 64; }
: "${REQUEST_RESTORE_HOST:?REQUEST_RESTORE_HOST is required}"
: "${REQUEST_RESTORE_NAME:?REQUEST_RESTORE_NAME is required}"
: "${REQUEST_RESTORE_USER:?REQUEST_RESTORE_USER is required}"
: "${REQUEST_RESTORE_PGPASSFILE:?REQUEST_RESTORE_PGPASSFILE is required}"

export RESTORE_DB_HOST="$REQUEST_RESTORE_HOST"
export RESTORE_DB_PORT="${REQUEST_RESTORE_PORT:-5432}"
export RESTORE_DB_NAME="$REQUEST_RESTORE_NAME"
export RESTORE_DB_USER="$REQUEST_RESTORE_USER"
export PGPASSFILE="$REQUEST_RESTORE_PGPASSFILE"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$script_dir/../integrated/restore-from-restic.sh" request-db "$1"
