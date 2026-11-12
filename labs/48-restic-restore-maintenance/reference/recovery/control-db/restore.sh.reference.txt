#!/usr/bin/env bash
set -Eeuo pipefail

[[ $# -eq 1 ]] || { printf 'usage: %s snapshot-id|latest\n' "$0" >&2; exit 64; }
: "${CONTROL_RESTORE_HOST:?CONTROL_RESTORE_HOST is required}"
: "${CONTROL_RESTORE_NAME:?CONTROL_RESTORE_NAME is required}"
: "${CONTROL_RESTORE_USER:?CONTROL_RESTORE_USER is required}"
: "${CONTROL_RESTORE_PGPASSFILE:?CONTROL_RESTORE_PGPASSFILE is required}"

export RESTORE_DB_HOST="$CONTROL_RESTORE_HOST"
export RESTORE_DB_PORT="${CONTROL_RESTORE_PORT:-5432}"
export RESTORE_DB_NAME="$CONTROL_RESTORE_NAME"
export RESTORE_DB_USER="$CONTROL_RESTORE_USER"
export PGPASSFILE="$CONTROL_RESTORE_PGPASSFILE"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$script_dir/../integrated/restore-from-restic.sh" control-db "$1"
