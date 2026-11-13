#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# Dandelion Restic Backup Script
# Target:
# - WordPress container files
# - MariaDB wordpress_db dump
# - HAProxy proxy configuration
# - Prometheus backup staging placeholder
# - Evidence file
# ============================================================

DATE="$(date +%F_%H-%M-%S)"
BACKUP_ROOT="/backup"
STAGING_DIR="${BACKUP_ROOT}/staging"
LOG_DIR="${BACKUP_ROOT}/logs"
LOG_FILE="${LOG_DIR}/dandelion-restic-backup-${DATE}.log"

WEB_HOST="web"
PROXY_HOST="proxy"
DB_CNF="/etc/mysql/backup/wp_backup.cnf"
WORDPRESS_IMAGE="dandelion-wordpress:v1"

RESTIC_ENV="/etc/restic/restic.env"

mkdir -p "${STAGING_DIR}/db"
mkdir -p "${STAGING_DIR}/wordpress"
mkdir -p "${STAGING_DIR}/haproxy"
mkdir -p "${STAGING_DIR}/prometheus"
mkdir -p "${STAGING_DIR}/evidence"
mkdir -p "${LOG_DIR}"

log() {
  echo "[$(date '+%F %T')] $*" | tee -a "${LOG_FILE}"
}

run_cmd() {
  log "RUN: $*"
  "$@" 2>&1 | tee -a "${LOG_FILE}"
}

log "============================================================"
log "Dandelion Restic Backup Started"
log "Date: ${DATE}"
log "Host: $(hostname)"
log "============================================================"

# ------------------------------------------------------------
# 1. Basic validation
# ------------------------------------------------------------
log "[1/7] Checking required files and commands"

if [ ! -f "${RESTIC_ENV}" ]; then
  log "ERROR: Restic env file not found: ${RESTIC_ENV}"
  exit 1
fi

if [ ! -f "${DB_CNF}" ]; then
  log "ERROR: DB backup config not found: ${DB_CNF}"
  exit 1
fi

command -v restic >/dev/null 2>&1 || { log "ERROR: restic not installed"; exit 1; }
command -v mysqldump >/dev/null 2>&1 || { log "ERROR: mysqldump not installed"; exit 1; }
command -v ssh >/dev/null 2>&1 || { log "ERROR: ssh not installed"; exit 1; }
command -v scp >/dev/null 2>&1 || { log "ERROR: scp not installed"; exit 1; }

# ------------------------------------------------------------
# 2. WordPress Swarm volume collection
# ------------------------------------------------------------
log "[2/7] Collecting WordPress Docker Swarm replica volumes"

run_cmd ssh "${WEB_HOST}" "sudo rm -rf /tmp/wordpress-volumes-backup"
run_cmd ssh "${WEB_HOST}" "sudo mkdir -p /tmp/wordpress-volumes-backup"

ssh "${WEB_HOST}" '
i=1
for container in $(docker ps --filter "ancestor=dandelion-wordpress:v1" --format "{{.Names}}"); do
  volume_path=$(docker inspect "$container" --format "{{range .Mounts}}{{if eq .Destination \"/var/www/html\"}}{{.Source}}{{end}}{{end}}")
  echo "container=${container} volume=${volume_path}"

  if [ -n "$volume_path" ]; then
    sudo tar -czf "/tmp/wordpress-volumes-backup/wordpress-replica-${i}-volume.tar.gz" -C "$volume_path" .
    i=$((i+1))
  fi
done
'

rm -rf "${STAGING_DIR}/wordpress"/*
mkdir -p "${STAGING_DIR}/wordpress"

run_cmd scp "${WEB_HOST}:/tmp/wordpress-volumes-backup/*.tar.gz" "${STAGING_DIR}/wordpress/"

run_cmd ssh "${WEB_HOST}" "sudo rm -rf /tmp/wordpress-volumes-backup"

log "WordPress Swarm replica volume files collected"
ls -lh "${STAGING_DIR}/wordpress" | tee -a "${LOG_FILE}"

# ------------------------------------------------------------
# 3. MariaDB dump
# ------------------------------------------------------------
log "[3/7] Creating MariaDB dump"

rm -f "${STAGING_DIR}/db/wordpress_db-primary.sql"

run_cmd sudo mysqldump \
  --defaults-extra-file="${DB_CNF}" \
  --single-transaction \
  --routines \
  --triggers \
  wordpress_db

sudo mysqldump \
  --defaults-extra-file="${DB_CNF}" \
  --single-transaction \
  --routines \
  --triggers \
  wordpress_db > "${STAGING_DIR}/db/wordpress_db-primary.sql"

log "DB dump created: ${STAGING_DIR}/db/wordpress_db-primary.sql"

# ------------------------------------------------------------
# 4. Proxy HAProxy config collection
# ------------------------------------------------------------
log "[4/7] Collecting HAProxy configuration"

rm -f "${STAGING_DIR}/haproxy/"*.tar.gz || true

if ssh "${PROXY_HOST}" "test -d /etc/haproxy"; then
  log "Detected /etc/haproxy on proxy node"
  run_cmd ssh "${PROXY_HOST}" "sudo tar -czf /tmp/haproxy-config.tar.gz -C /etc haproxy"
  run_cmd scp "${PROXY_HOST}:/tmp/haproxy-config.tar.gz" "${STAGING_DIR}/haproxy/haproxy-config.tar.gz"
  run_cmd ssh "${PROXY_HOST}" "sudo rm -f /tmp/haproxy-config.tar.gz"
else
  log "/etc/haproxy not found. Trying HAProxy container config."

  HAPROXY_CONTAINER="$(ssh "${PROXY_HOST}" "docker ps --format '{{.Names}}' | grep -i haproxy | head -n 1" || true)"

  if [ -n "${HAPROXY_CONTAINER}" ]; then
    log "Detected HAProxy container: ${HAPROXY_CONTAINER}"
    run_cmd ssh "${PROXY_HOST}" "sudo rm -rf /tmp/haproxy-container-config /tmp/haproxy-container-config.tar.gz"
    run_cmd ssh "${PROXY_HOST}" "sudo docker cp ${HAPROXY_CONTAINER}:/usr/local/etc/haproxy /tmp/haproxy-container-config"
    run_cmd ssh "${PROXY_HOST}" "sudo tar -czf /tmp/haproxy-container-config.tar.gz -C /tmp haproxy-container-config"
    run_cmd scp "${PROXY_HOST}:/tmp/haproxy-container-config.tar.gz" "${STAGING_DIR}/haproxy/haproxy-container-config.tar.gz"
    run_cmd ssh "${PROXY_HOST}" "sudo rm -rf /tmp/haproxy-container-config /tmp/haproxy-container-config.tar.gz"
  else
    log "WARNING: HAProxy configuration source not found."
    echo "HAProxy configuration was not collected at ${DATE}" > "${STAGING_DIR}/haproxy/README.md"
  fi
fi

# ------------------------------------------------------------
# 5. Prometheus placeholder
# ------------------------------------------------------------
log "[5/7] Preparing Prometheus staging placeholder"

cat > "${STAGING_DIR}/prometheus/README.md" <<PROMEOF
# Prometheus Backup Staging

Status: Prepared
Date: ${DATE}

Prometheus and exporters are not fully deployed yet.
Actual Prometheus configuration backup will be collected after monitoring setup is completed.

Planned targets:
- /etc/prometheus/prometheus.yml
- Prometheus rule files
- node_exporter target configuration
- cAdvisor target configuration
- mysqld_exporter target configuration
- blackbox_exporter configuration
PROMEOF

# ------------------------------------------------------------
# 6. Evidence file
# ------------------------------------------------------------
log "[6/7] Creating evidence file"

cat > "${STAGING_DIR}/evidence/restic-backup-evidence-${DATE}.txt" <<EVEOF
Dandelion Restic Backup Evidence

Date: ${DATE}
Backup Node: $(hostname)
Repository: /backup/restic-repo

Collected Targets:
- WordPress container files: ${STAGING_DIR}/wordpress/wordpress-html.tar.gz
- MariaDB dump: ${STAGING_DIR}/db/wordpress_db-primary.sql
- HAProxy configuration: ${STAGING_DIR}/haproxy
- Prometheus staging placeholder: ${STAGING_DIR}/prometheus/README.md

Validation:
- restic backup
- restic snapshots
- restic check
EVEOF

# ------------------------------------------------------------
# 7. Restic backup
# ------------------------------------------------------------
log "[7/7] Running Restic backup"

sudo bash -c "source ${RESTIC_ENV} && restic backup \
  ${STAGING_DIR}/db \
  ${STAGING_DIR}/wordpress \
  ${STAGING_DIR}/haproxy \
  ${STAGING_DIR}/prometheus \
  ${STAGING_DIR}/evidence \
  --tag dandelion \
  --tag automated-backup \
  --tag ${DATE}" 2>&1 | tee -a "${LOG_FILE}"

log "Running restic snapshots"
sudo bash -c "source ${RESTIC_ENV} && restic snapshots" 2>&1 | tee -a "${LOG_FILE}"

log "Running restic check"
sudo bash -c "source ${RESTIC_ENV} && restic check" 2>&1 | tee -a "${LOG_FILE}"

log "============================================================"
log "Dandelion Restic Backup Completed"
log "Log file: ${LOG_FILE}"
log "============================================================"
