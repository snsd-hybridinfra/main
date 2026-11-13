#!/bin/bash

### TODO : cinder 볼륨으로 조건 변경

result_backup=false

ping -c 3 backup
ping_result_backup=$?

ssh  -o ConnectTimeout=2 -i /home/ubuntu/.ssh/dandelion.pem  ubuntu@backup 'df -h'
ssh_result_backup=$?

if [ $ping_result_backup -eq 0 ] && [ $ssh_result_backup -eq 0 ]
then
  result_backup=true
  echo 'success backup'
fi

export result_backup=$result_backup