<!-- STATUS: COMPLETE -->

# Troubleshooting Guide

## 1. 문서 목적

본 문서는 Team Dandelion 프로젝트에서 발생할 수 있는 주요 장애 상황과 점검 절차를 정의한다.

본 프로젝트는 Phase 기반 구현 로드맵을 사용한다.

~~~text
Phase 1: 필수 구성 및 기본 검증 단계
Phase 2: 운영 확장 및 검증 고도화 단계
Phase 3: 도전 확장 단계
Out of Scope: 제외 범위
~~~

본 문서는 Phase 1 필수 구성인 OpenStack, SSH, Ansible, Docker, HAProxy, WordPress, MariaDB, Backup / Restore 검증 과정에서 발생할 수 있는 문제를 중심으로 작성한다.

---

## 2. 기본 트러블슈팅 원칙

문제가 발생하면 서비스부터 수정하지 않고 아래 순서로 확인한다.

~~~text
1. OpenStack 인스턴스 상태
2. 네트워크 / 라우터 / 서브넷
3. 보안그룹
4. Floating IP 또는 포트포워딩
5. SSH 접속
6. Ansible Inventory
7. Ansible ping
8. Docker 서비스 상태
9. 컨테이너 상태
10. 포트 리스닝 상태
11. 애플리케이션 로그
12. 백업 / 복구 절차
~~~

---

## 3. 공통 확인 명령어

## 3.1 서버 기본 상태

~~~bash
hostname
cat /etc/os-release
ip addr
ip route
uptime
df -h
free -h
top
~~~

---

## 3.2 네트워크 확인

~~~bash
ping TARGET_IP
curl -I http://TARGET_IP
nc -zv TARGET_IP PORT
sudo ss -tulnp
~~~

---

## 3.3 Docker 확인

~~~bash
docker --version
docker compose version
sudo systemctl status docker
docker ps
docker ps -a
docker logs CONTAINER_NAME --tail 50
docker system df
docker stats
~~~

---

## 3.4 Ansible 확인

~~~bash
cd ansible
ansible --version
ansible-inventory --list
ansible all -m ping
ansible-playbook site.yml --syntax-check
ansible-playbook site.yml -vv
~~~

---

## 4. OpenStack 인스턴스 장애

## 4.1 증상

| 증상 |
|---|
| 인스턴스가 ACTIVE 상태가 아님 |
| 인스턴스 생성 실패 |
| 인스턴스 부팅 후 SSH 접속 불가 |
| 콘솔 로그에 부팅 오류 발생 |
| 리소스 부족으로 인스턴스 생성 실패 |

---

## 4.2 확인 명령어

~~~bash
openstack server list
openstack server show INSTANCE_NAME
openstack console log show INSTANCE_NAME
openstack hypervisor stats show
openstack flavor list
openstack image list
~~~

---

## 4.3 조치 방향

| 원인 | 조치 |
|---|---|
| 리소스 부족 | 작은 flavor 사용 또는 불필요한 인스턴스 삭제 |
| 이미지 문제 | Ubuntu 이미지 상태 확인 |
| 네트워크 미연결 | 네트워크 / 서브넷 / 라우터 연결 확인 |
| Key Pair 문제 | 올바른 Key Pair 선택 여부 확인 |
| Security Group 문제 | SSH 22 허용 여부 확인 |

---

## 5. SSH 접속 장애

## 5.1 증상

| 증상 |
|---|
| Permission denied |
| Connection timed out |
| No route to host |
| Connection refused |
| Ansible ping 실패 |

---

## 5.2 확인 순서

~~~text
1. 인스턴스 ACTIVE 상태 확인
2. Private IP / Floating IP 확인
3. Key Pair 확인
4. Key 권한 확인
5. Security Group SSH 22 허용 확인
6. 포트포워딩 설정 확인
7. 사용자명 ubuntu 확인
~~~

---

## 5.3 확인 명령어

~~~bash
chmod 400 ~/.ssh/dandelion-key.pem
ssh -i ~/.ssh/dandelion-key.pem ubuntu@NODE_IP
ssh -vvv -i ~/.ssh/dandelion-key.pem ubuntu@NODE_IP
~~~

---

## 5.4 조치 방향

| 원인 | 조치 |
|---|---|
| Key 권한 오류 | chmod 400 적용 |
| 사용자명 오류 | ubuntu 사용자 사용 |
| IP 오류 | OpenStack server list에서 IP 재확인 |
| 보안그룹 오류 | SSH 22 허용 |
| 포트포워딩 오류 | Host / Router forwarding 규칙 재확인 |

---

## 6. Ansible 장애

## 6.1 증상

| 증상 |
|---|
| ansible all -m ping 실패 |
| UNREACHABLE 발생 |
| Permission denied 발생 |
| inventory host 누락 |
| playbook syntax error |
| playbook 실행 중 task 실패 |

---

## 6.2 확인 명령어

~~~bash
cd ansible
cat ansible.cfg
cat inventory.ini
ansible-inventory --list
ansible all -m ping -vvv
ansible-playbook site.yml --syntax-check
ansible-playbook site.yml -vv
~~~

---

## 6.3 주요 원인과 조치

| 원인 | 조치 |
|---|---|
| inventory IP 오류 | 실제 Private IP 또는 접속 IP로 수정 |
| SSH Key 경로 오류 | ansible_ssh_private_key_file 확인 |
| remote_user 오류 | ubuntu 사용자 확인 |
| host_key 문제 | host_key_checking=False 확인 |
| YAML 문법 오류 | syntax-check 결과 기준 수정 |
| become 권한 오류 | become: true 적용 여부 확인 |
| 패키지 설치 실패 | apt update 및 네트워크 확인 |

---

## 7. Docker 설치 장애

## 7.1 증상

| 증상 |
|---|
| docker 명령어 없음 |
| Docker daemon not running |
| permission denied |
| docker compose 명령어 없음 |
| image pull 실패 |

---

## 7.2 확인 명령어

~~~bash
docker --version
docker compose version
sudo systemctl status docker
sudo systemctl start docker
sudo systemctl enable docker
groups
df -h
ping 8.8.8.8
~~~

---

## 7.3 조치 방향

| 원인 | 조치 |
|---|---|
| Docker 미설치 | playbook 또는 apt로 Docker 설치 |
| Docker 서비스 중지 | systemctl start docker |
| 권한 문제 | usermod -aG docker ubuntu 후 재접속 |
| Compose 미설치 | docker-compose-plugin 설치 |
| 디스크 부족 | 불필요한 image / container / backup 삭제 |
| 외부 통신 불가 | NAT / Router / DNS 확인 |

---

## 8. Proxy Node / HAProxy 장애

## 8.1 증상

| 증상 |
|---|
| Proxy Node 접속 불가 |
| curl http://PROXY_NODE_IP 실패 |
| HAProxy 컨테이너 종료 |
| 503 Service Unavailable |
| Web Node backend 연결 실패 |

---

## 8.2 확인 명령어

~~~bash
docker ps
docker ps -a
docker logs dandelion-haproxy --tail 100
sudo ss -tulnp | grep ':80'
cat /opt/dandelion/proxy/haproxy.cfg
curl -I http://WEB_NODE_PRIVATE_IP
~~~

---

## 8.3 주요 원인과 조치

| 원인 | 조치 |
|---|---|
| HAProxy 컨테이너 미실행 | docker compose up -d 재실행 |
| haproxy.cfg 문법 오류 | 설정 파일 문법 수정 |
| Web Node IP 오류 | backend IP를 실제 Web Node Private IP로 수정 |
| Web Node 80 미응답 | Web Node WordPress 상태 확인 |
| 보안그룹 오류 | Proxy Node → Web Node 80 허용 |
| Proxy 80 미오픈 | Proxy Node 보안그룹 80 허용 |

---

## 9. Web Node / WordPress 장애

## 9.1 증상

| 증상 |
|---|
| WordPress 컨테이너가 실행되지 않음 |
| WordPress 화면 접속 불가 |
| Error establishing a database connection |
| 500 Internal Server Error |
| Proxy는 동작하지만 Web 응답 없음 |

---

## 9.2 확인 명령어

~~~bash
docker ps
docker ps -a
docker logs dandelion-wordpress --tail 100
sudo ss -tulnp | grep ':80'
curl -I http://localhost
curl -I http://WEB_NODE_PRIVATE_IP
nc -zv DB_NODE_PRIVATE_IP 3306
~~~

---

## 9.3 주요 원인과 조치

| 원인 | 조치 |
|---|---|
| WordPress 컨테이너 미실행 | docker compose up -d 재실행 |
| 이미지 build 실패 | Dockerfile / custom.ini 경로 확인 |
| DB Host 오류 | WORDPRESS_DB_HOST 값 확인 |
| DB User / Password 오류 | MariaDB 환경변수와 일치 여부 확인 |
| DB 3306 접근 불가 | 보안그룹 및 DB 컨테이너 확인 |
| Web Node 80 미오픈 | 컨테이너 포트 및 보안그룹 확인 |

---

## 10. DB Node / MariaDB 장애

## 10.1 증상

| 증상 |
|---|
| MariaDB 서비스가 실행되지 않음 |
| Web Node에서 DB 연결 실패 |
| 3306 포트가 열려 있지 않음 |
| WordPress database connection error |
| DB dump 실패 |

---

## 10.2 확인 명령어

~~~bash
docker ps
docker ps -a
docker logs mariadb --tail 100
sudo ss -tulnp | grep ':3306'
docker exec -it mariadb mariadb -u root -p
~~~

Web Node에서 확인:

~~~bash
nc -zv DB_NODE_PRIVATE_IP 3306
~~~

Backup / Validation Node에서 확인:

~~~bash
nc -zv DB_NODE_PRIVATE_IP 3306
~~~

---

## 10.3 주요 원인과 조치

| 원인 | 조치 |
|---|---|
| MariaDB 서비스 미실행 | docker compose up -d 재실행 |
| 환경변수 오류 | MYSQL_DATABASE / MYSQL_USER / MYSQL_PASSWORD 확인 |
| volume 권한 문제 | Docker volume 재확인 |
| 3306 미오픈 | ports 설정 및 ss 확인 |
| 보안그룹 오류 | Web Node / Backup Node에서만 3306 허용 |
| 디스크 부족 | df -h 확인 후 정리 |

---

## 11. Backup 장애

## 11.1 증상

| 증상 |
|---|
| backup.sh 실행 실패 |
| MariaDB dump 파일 생성 실패 |
| WordPress files archive 생성 실패 |
| 백업 파일 크기가 0 byte |
| 백업 저장 경로 없음 |
| Permission denied 발생 |

---

## 11.2 확인 명령어

~~~bash
bash scripts/backup.sh
echo $?
ls -lh backup/
df -h
free -h
nc -zv DB_NODE_PRIVATE_IP 3306
curl -I http://WEB_NODE_PRIVATE_IP
~~~

DB Node에서 dump 확인:

~~~bash
docker exec mariadb mariadb-dump -u root -p wordpress > wordpress_db.sql
~~~

---

## 11.3 주요 원인과 조치

| 원인 | 조치 |
|---|---|
| DB 연결 실패 | DB IP / 보안그룹 / 계정 정보 확인 |
| 저장 경로 없음 | backup 디렉터리 생성 |
| 권한 문제 | chmod 또는 sudo 사용 |
| 디스크 부족 | 오래된 백업 파일 정리 |
| WordPress files 경로 오류 | 컨테이너 volume 경로 확인 |
| Cinder mount 미완료 | Phase 2인 경우 /backup 마운트 확인 |

---

## 12. Restore 장애

## 12.1 증상

| 증상 |
|---|
| restore.md 절차대로 복구 불가 |
| DB import 실패 |
| WordPress files 복원 실패 |
| 복구 후 WordPress 접속 불가 |
| 기존 데이터 덮어쓰기 위험 발생 |

---

## 12.2 확인 항목

| 확인 항목 | 기준 |
|---|---|
| 백업 파일 존재 | wordpress_db.sql, wordpress_files.tar.gz |
| 파일 크기 | 0 byte 아님 |
| DB 컨테이너 상태 | MariaDB running |
| WordPress 컨테이너 상태 | WordPress running |
| 복구 명령어 | restore.md에 명확히 기록 |
| 주의사항 | 기존 데이터 덮어쓰기 위험 명시 |

---

## 12.3 조치 방향

| 원인 | 조치 |
|---|---|
| 백업 파일 없음 | backup.sh 재실행 |
| DB import 계정 오류 | DB 계정 및 권한 확인 |
| 파일 복원 경로 오류 | WordPress volume 경로 확인 |
| 복구 후 접속 불가 | WordPress / DB / Proxy 순서로 재확인 |
| 운영 데이터 위험 | 테스트 환경에서만 복구 검증 |

---

## 13. Phase 2 Monitoring 장애

## 13.1 증상

| 증상 |
|---|
| node_exporter metrics 미출력 |
| cAdvisor metrics 미출력 |
| Prometheus target DOWN |
| Grafana datasource 연결 실패 |
| Dashboard 데이터 없음 |

---

## 13.2 확인 명령어

~~~bash
curl http://TARGET_NODE_IP:9100/metrics
curl http://TARGET_NODE_IP:8080/metrics
curl http://PROMETHEUS_IP:9090
curl http://GRAFANA_IP:3000
docker ps
docker logs prometheus --tail 50
docker logs grafana --tail 50
~~~

---

## 13.3 조치 방향

| 원인 | 조치 |
|---|---|
| exporter 미실행 | node_exporter / cAdvisor 컨테이너 확인 |
| 포트 미허용 | 보안그룹 9100 / 8080 확인 |
| Prometheus 설정 오류 | prometheus.yml target IP 확인 |
| Grafana datasource 오류 | Prometheus URL 확인 |
| 리소스 부족 | Monitoring stack 중단 또는 Phase 2 제외 |

---

## 14. Phase 2 Cinder Backup Volume 장애

## 14.1 증상

| 증상 |
|---|
| Cinder Volume 생성 실패 |
| Volume attach 실패 |
| Backup Node에서 디스크가 보이지 않음 |
| /backup mount 실패 |
| backup.sh 결과물이 Cinder에 저장되지 않음 |

---

## 14.2 확인 명령어

~~~bash
openstack volume list
openstack volume show VOLUME_NAME
openstack server show BACKUP_NODE
lsblk
sudo fdisk -l
df -h
mount | grep backup
ls -lh /backup
~~~

---

## 14.3 조치 방향

| 원인 | 조치 |
|---|---|
| Volume 상태 오류 | volume status 확인 |
| attach 실패 | server / volume 상태 확인 |
| 디스크 인식 실패 | lsblk / dmesg 확인 |
| mount 실패 | filesystem 생성 여부 확인 |
| 권한 문제 | /backup ownership 확인 |
| 백업 경로 오류 | backup.sh 저장 경로 수정 |

Cinder Volume은 DB 원본 데이터 저장소가 아니라 Backup / Validation Node의 백업 저장소로 사용한다.

---

## 15. Phase 3 Load Balancing 장애

## 15.1 증상

| 증상 |
|---|
| Web Node 2 접속 불가 |
| HAProxy backend 2개 등록 실패 |
| roundrobin 응답이 한 노드로만 감 |
| Web Node 1 중지 시 Web Node 2 응답 실패 |
| 공통 DB 연결 실패 |

---

## 15.2 확인 명령어

~~~bash
docker ps
docker logs dandelion-haproxy --tail 100
cat /opt/dandelion/proxy/haproxy.cfg
curl -I http://WEB_NODE_1_IP
curl -I http://WEB_NODE_2_IP
for i in {1..10}; do curl http://PROXY_NODE_IP/health.html; done
nc -zv DB_NODE_PRIVATE_IP 3306
~~~

---

## 15.3 조치 방향

| 원인 | 조치 |
|---|---|
| Web Node 2 미실행 | WordPress 컨테이너 확인 |
| backend IP 오류 | haproxy.cfg IP 수정 |
| 보안그룹 오류 | Proxy → Web Node 1/2 80 허용 |
| health check 실패 | health.html 또는 backend check 수정 |
| DB 연결 실패 | Web Node 2 → DB Node 3306 허용 |
| 파일 동기화 문제 | 이번 범위에서는 제외하고 LB 응답 검증만 수행 |

---

## 16. 리소스 부족 대응

## 16.1 증상

| 증상 |
|---|
| 인스턴스 생성 실패 |
| Docker image pull 실패 |
| 컨테이너가 자주 종료됨 |
| WordPress 응답 지연 |
| MariaDB 응답 지연 |
| backup.sh 실패 |
| Prometheus / Grafana 실행 불가 |

---

## 16.2 확인 명령어

~~~bash
free -h
df -h
top
docker stats
docker system df
docker ps -a
du -sh backup/*
~~~

---

## 16.3 조치 우선순위

| 순서 | 조치 |
|---:|---|
| 1 | 불필요한 stopped container 삭제 |
| 2 | 불필요한 image 삭제 |
| 3 | 오래된 backup 파일 정리 |
| 4 | Phase 2 Monitoring stack 중단 |
| 5 | Web Node 2 등 Phase 3 확장 중단 |
| 6 | flavor 상향 또는 리소스 증설 |
| 7 | Phase 1 필수 구성 중심으로 범위 축소 |

---

## 17. 장애 기록 템플릿

장애 발생 시 아래 형식으로 기록한다.

~~~text
## Incident Title

### 발생 일시
YYYY-MM-DD HH:MM

### 담당자
이름 / 역할

### 발생 위치
OpenStack / SSH / Ansible / Proxy / Web / DB / Backup / Monitoring

### 증상
무엇이 실패했는지 작성

### 확인 명령어
실행한 명령어 작성

### 원인
확인된 원인 작성

### 조치
수행한 해결 방법 작성

### 결과
복구 여부 작성

### 캡처
관련 캡처 파일 경로 작성

### 재발 방지
다음 실행 전 확인할 항목 작성
~~~

---

## 18. 최종 장애 대응 메시지

~~~text
본 프로젝트의 장애 대응은 기능을 무리하게 늘리는 것이 아니라,
Phase 1 필수 구성의 안정성을 우선한다.

문제가 발생하면 OpenStack, SSH, Ansible, Docker, Proxy, Web, DB, Backup 순서로 원인을 좁혀간다.

Phase 1이 안정화되지 않으면 Phase 2와 Phase 3 확장은 중단하고,
최종 발표 가능한 기본 운영 흐름을 먼저 완성한다.
~~~



