#!/bin/bash

### TODO : 도커 컨테이너로 조건 변경 && 백업본 교체 조건 확인 및 교체
result_web2=false

ping -c 3 web2
ping_result_web2=$?

curl -fsS http://web2
curl_result_web2=$?

ssh  -o ConnectTimeout=2 -i /home/ubuntu/.ssh/dandelion.pem ubuntu@web2 'docker container ls | grep dandelion-wordpress | grep healthy'
ssh_result_web2=$?

if [ $ping_result_web2 -eq 0 ] && [ $curl_result_web2 -eq 0 ] && [ $ssh_result_web2 -eq 0 ]
then
  result_web2=true
  echo 'success web2'
else
  ssh -o ConnectTimeout=2 -i /home/ubuntu/.ssh/dandelion.pem ubuntu@web2 'docker container restart dandelion-wordpress | grep healthy'
  #ssh -o ConnectTimeout=2  -i /home/ubuntu/.ssh/dandelion.pem \
  #ubuntu@backup 'cat $(ls -td /tmp/backup/* | head -n 1)/backup-web2.tar.gz' | \
  #ssh -o ConnectTimeout=2  -i /home/ubuntu/.ssh/dandelion.pem \
  ##ubuntu@web2 "docker exec -i dandelion-wp tar xzf - -C /"
fi

export result_web2=$result_web2