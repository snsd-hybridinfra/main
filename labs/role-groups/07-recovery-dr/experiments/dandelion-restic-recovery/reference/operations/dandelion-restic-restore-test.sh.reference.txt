#!/usr/bin/env bash
set -euo pipefail

RESTIC_ENV="/etc/restic/restic.env"
RESTORE_DIR="/backup/restore-test"
DATE="$(date +%F_%H-%M-%S)"
LOG_FILE="/backup/logs/dandelion-restic-restore-test-${DATE}.log"

mkdir -p "${RESTORE_DIR}"
rm -rf "${RESTORE_DIR:?}"/*

echo "[INFO] Restic restore test started at ${DATE}" | tee -a "${LOG_FILE}"

sudo bash -c "source ${RESTIC_ENV} && restic restore latest --target ${RESTORE_DIR}" 2>&1 | tee -a "${LOG_FILE}"

echo "[INFO] Restored files:" | tee -a "${LOG_FILE}"
find "${RESTORE_DIR}" -maxdepth 6 -type f | sort | tee -a "${LOG_FILE}"

echo "[INFO] Restore test completed" | tee -a "${LOG_FILE}"
