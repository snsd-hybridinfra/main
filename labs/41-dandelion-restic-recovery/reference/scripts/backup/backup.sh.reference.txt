#!/bin/bash
date=$(date +%Y-%m-%d)
mkdir -p "/tmp/backup/$date"
workdir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "${workdir}/db-backup.sh"
source "${workdir}/web-backup.sh"

echo -e "
==== $(date +%Y-%m-%d_%H:%M:%S) backup results ====
db_backup_result=$db_backup_result
web1_backup_result=$web1_backup_result
web2_backup_result=$web2_backup_result
" >> /tmp/backup/$date/backup_results.txt