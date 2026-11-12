
### TODO : 도커 컨테이너로 조건 변경 && 백업본 교체 조건 확인 및 교체
result_web1=false

ping -c 3 web1
ping_result_web1=$?

curl -fsS http://web1
curl_result_web1=$?

ssh  -o ConnectTimeout=2 -i /home/ubuntu/.ssh/dandelion.pem ubuntu@web1 'docker container ls | grep dandelion-wordpress | grep healthy'
ssh_result_web1=$?

if [ $ping_result_web1 -eq 0 ] && [ $curl_result_web1 -eq 0 ] && [ $ssh_result_web1 -eq 0 ]
then
  result_web1=true
  echo 'success web1'
else
  ssh -o ConnectTimeout=2 -i /home/ubuntu/.ssh/dandelion.pem ubuntu@web1 'docker container restart dandelion-wordpress | grep healthy'
  #ssh -o ConnectTimeout=2  -i /home/ubuntu/.ssh/dandelion.pem \
  #ubuntu@backup 'cat $(ls -td /tmp/backup/* | head -n 1)/backup-web1.tar.gz' | \
  #ssh -o ConnectTimeout=2  -i /home/ubuntu/.ssh/dandelion.pem \
  ##ubuntu@web1 "docker exec -i dandelion-wp tar xzf - -C /"
fi


export result_web1=$result_web1