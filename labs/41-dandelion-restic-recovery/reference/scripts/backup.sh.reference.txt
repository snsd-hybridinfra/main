<!-- STATUS: TEMPLATE -->
# TEMPLATE: 기본틀 파일입니다. 실제 환경 값 반영 및 실행 검증 후 이 표시를 제거하세요.
#!/bin/bash

DATE=$(date +%Y%m%d_%H%M%S)
SOURCE_DIR="/var/www/html"
BACKUP_DIR="/backup"
BACKUP_FILE="web_backup_${DATE}.tar.gz"

mkdir -p ${BACKUP_DIR}
tar -czf ${BACKUP_DIR}/${BACKUP_FILE} ${SOURCE_DIR}

echo "Backup completed: ${BACKUP_DIR}/${BACKUP_FILE}"
