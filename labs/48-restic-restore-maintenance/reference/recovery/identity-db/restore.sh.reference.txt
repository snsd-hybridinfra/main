#!/usr/bin/env bash
set -Eeuo pipefail

[[ $# -eq 1 ]] || { printf 'usage: %s snapshot-id|latest\n' "$0" >&2; exit 64; }
: "${IDENTITY_RESTORE_HOST:?IDENTITY_RESTORE_HOST is required}"
: "${IDENTITY_RESTORE_NAME:?IDENTITY_RESTORE_NAME is required}"
: "${IDENTITY_RESTORE_USER:?IDENTITY_RESTORE_USER is required}"
: "${IDENTITY_RESTORE_PGPASSFILE:?IDENTITY_RESTORE_PGPASSFILE is required}"

export RESTORE_DB_HOST="$IDENTITY_RESTORE_HOST"
export RESTORE_DB_PORT="${IDENTITY_RESTORE_PORT:-5432}"
export RESTORE_DB_NAME="$IDENTITY_RESTORE_NAME"
export RESTORE_DB_USER="$IDENTITY_RESTORE_USER"
export PGPASSFILE="$IDENTITY_RESTORE_PGPASSFILE"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$script_dir/../integrated/restore-from-restic.sh" identity-db "$1"
