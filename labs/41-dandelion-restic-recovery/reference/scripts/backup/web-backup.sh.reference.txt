#!/bin/bash

###=============================================================================================================================  web1 backup
ping -c 3 web1; ping -c 3 web2

ssh -i /home/ubuntu/.ssh/dandelion.pem ubuntu@web1 'docker exec dandelion-wordpress tar czf - /var/www/html' > /tmp/backup/$date/backup-web1.tar.gz

web1_backup_result=$?
if [ $web1_backup_result -eq 0 ]
then
        echo 'success web1'
        web1_backup_result=true
else
        echo 'failed web1'
        web1_backup_result=false
fi




#ssh -i /home/ubuntu/.ssh/dandelion.pem ubuntu@web2 'docker exec dandelion-wordpress tar czf - /var/www/html' > /tmp/backup/$date/backup-web2.tar.gz
#
#web2_backup_result=$?
#if [ $web2_backup_result -eq 0 ]
#then
#       echo 'success web2'
#       web2_backup_result=true
#else
#       echo 'failed web2'
#       web2_backup_result=false
#fi




export web1_backup_result=$web1_backup_result
export web2_backup_result=$web2_backup_result