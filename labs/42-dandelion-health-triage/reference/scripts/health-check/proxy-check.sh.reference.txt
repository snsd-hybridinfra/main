#!/bin/bash


result_proxy=false

ping -c 3 proxy
ping_result_proxy=$?

ssh  -o ConnectTimeout=2  -i /home/ubuntu/.ssh/dandelion.pem  ubuntu@proxy 'sudo systemctl status haproxy | grep active'
ssh_result_proxy=$?

if [ $ping_result_proxy -eq 0 ] && [ $ssh_result_proxy -eq 0 ]
then
  result_proxy=true
  echo 'success proxy'
else
  ssh  -o ConnectTimeout=2 -i /home/ubuntu/.ssh/dandelion.pem  ubuntu@proxy 'sudo systemctl restart haproxy'
fi

export result_proxy=$result_proxy