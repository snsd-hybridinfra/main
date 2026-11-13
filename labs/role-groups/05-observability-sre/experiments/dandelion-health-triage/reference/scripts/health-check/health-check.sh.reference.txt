#!/bin/bash

date=$(date +%Y-%m-%d)

mkdir -p "/tmp/monitoring/$date"
work_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
### TODO : 컴퓨팅 자원과 저장 공간 확인 및 조치

source "$work_dir/web1-check.sh"
#source "$work_dir/web2-check.sh"
source "$work_dir/db-check.sh"
source "$work_dir/proxy-check.sh"
source "$work_dir/backup-check.sh"
source "$work_dir/control-check.sh"


echo -e "
==== $(date +%Y-%m-%d_%H:%M:%S) check results ====
result_web1=$result_web1
result_web2=$result_web2
result_db=$result_db
result_proxy=$result_proxy
result_backup=$result_backup
result_control=$result_control
" >> /tmp/monitoring/$date/check_results.txt