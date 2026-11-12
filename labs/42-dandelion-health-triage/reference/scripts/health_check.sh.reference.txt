<!-- STATUS: TEMPLATE -->
# TEMPLATE: 기본틀 파일입니다. 실제 환경 값 반영 및 실행 검증 후 이 표시를 제거하세요.
#!/bin/bash

echo "===== Hostname ====="
hostname

echo "===== Uptime ====="
uptime

echo "===== Memory ====="
free -h

echo "===== Disk ====="
df -h

echo "===== IP Address ====="
ip addr

echo "===== Listening Ports ====="
ss -tulnp

echo "===== Docker Status ====="
systemctl is-active docker

echo "===== Running Containers ====="
docker ps

echo "===== HTTP Check ====="
curl -I http://localhost







