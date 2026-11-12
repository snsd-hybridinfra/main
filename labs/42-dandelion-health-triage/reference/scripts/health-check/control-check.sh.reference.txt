#!/bin/bash


result_control=false

ping -c 3 control
ping_result_control=$?

ssh  -o ConnectTimeout=2 -i /home/ubuntu/.ssh/dandelion.pem  ubuntu@control 'free -mh'
ssh_result_control=$?

if [ $ping_result_control -eq 0 ] && [ $ssh_result_control -eq 0 ]
then
  result_control=true
  echo 'success control'
fi


export result_control=$result_control