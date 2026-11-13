<!-- STATUS: COMPLETE -->

# Server Setup

## 1. 문서 목적

본 문서는 Team Dandelion 프로젝트의 서버 구성 기준을 정의한다.

본 프로젝트는 Phase 1에서 Control Node, Proxy Node, Web Node, DB Node, Backup / Validation Node를 분리하여 구성한다.

각 서버는 Ubuntu 기반 인스턴스로 구성하며, Ansible을 통해 공통 패키지 설치, Docker 설치, WordPress 컨테이너 배포, HAProxy 컨테이너 배포, MariaDB 직접 설치 및 서비스 구성을 자동화한다.

---

## 2. Phase 기반 서버 구성 전략

본 프로젝트는 Phase 기반 구현 로드맵을 사용한다.

~~~text
Phase 1: 필수 구성 및 기본 검증 단계
Phase 2: 운영 확장 및 검증 고도화 단계
Phase 3: 도전 확장 단계
Out of Scope: 제외 범위
~~~

Phase 1에서는 다음 서버 구성을 필수로 한다.

~~~text
Control Node
→ Ansible 실행

Proxy Node
→ HAProxy Container

Web Node
→ Custom WordPress Container

DB Node
→ MariaDB Package Install
→ MariaDB systemd Service

Backup / Validation Node
→ health_check.sh
→ backup.sh
→ mysqldump
→ restore.md 검증
~~~

---

## 3. 서버 역할 정의

| Node | Role | Required Component |
|---|---|---|
| Control Node | Ansible 실행 및 전체 자동화 제어 | Ansible |
| Proxy Node | 외부 HTTP 접속 진입점 | Docker, HAProxy Container |
| Web Node | WordPress 서비스 실행 | Docker, Custom WordPress Container |
| DB Node | WordPress 데이터 저장 | MariaDB Package, MariaDB Service |
| Backup / Validation Node | 상태 점검, 백업, 복구 검증 | health_check.sh, backup.sh, mysqldump client |

---

## 4. 공통 서버 기본 설정

모든 Ubuntu 인스턴스에서 기본적으로 확인해야 할 항목은 다음과 같다.

| 항목 | 확인 내용 |
|---|---|
| OS | Ubuntu 기반 인스턴스 |
| SSH | Control Node에서 접속 가능 |
| Package Update | apt update 가능 |
| Time | 서버 시간 확인 |
| Disk | df -h 기준 디스크 여유 공간 확인 |
| Memory | free -h 기준 메모리 확인 |
| Network | 노드 간 통신 가능 |

확인 명령어:

~~~bash
hostname
cat /etc/os-release
ip addr
ip route
df -h
free -h
uptime
~~~

---

## 5. Docker 설치 기준

Docker는 Proxy Node와 Web Node에 필수로 설치한다.

| Node | Docker 필요 여부 | 이유 |
|---|---|---|
| Proxy Node | 필요 | HAProxy Container 실행 |
| Web Node | 필요 | Custom WordPress Container 실행 |
| DB Node | 불필요 | MariaDB 직접 설치 |
| Backup / Validation Node | 선택 | 백업/검증 스크립트 방식에 따라 선택 |
| Control Node | 선택 | Ansible 실행 중심 |

Docker 설치 후 다음 명령어로 확인한다.

~~~bash
docker --version
docker compose version
sudo systemctl status docker
~~~

Docker 서비스가 실행 중이어야 한다.

~~~bash
sudo systemctl enable docker
sudo systemctl start docker
~~~

권한이 필요한 경우 ubuntu 사용자를 docker 그룹에 추가한다.

~~~bash
sudo usermod -aG docker ubuntu
~~~

적용 후 재접속한다.

---

## 6. Proxy Node 구성

## 6.1 역할

Proxy Node는 외부 HTTP 요청을 받아 Web Node로 전달한다.

Phase 1에서 Proxy Node는 HAProxy HTTP Reverse Proxy까지만 담당한다.

~~~text
Client
→ Proxy Node:80
→ HAProxy Container
→ Web Node:80
~~~

HTTPS와 HTTP to HTTPS Redirect는 Phase 2에서 처리한다.

---

## 6.2 HAProxy 컨테이너 구성

권장 경로:

~~~text
docker/proxy/
├── docker-compose.yml
└── haproxy.cfg
~~~

예시 `docker/proxy/docker-compose.yml`:

~~~yaml
services:
  haproxy:
    image: haproxy:2.9
    container_name: dandelion-haproxy
    restart: unless-stopped
    ports:
      - "80:80"
    volumes:
      - ./haproxy.cfg:/usr/local/etc/haproxy/haproxy.cfg:ro
~~~

예시 `docker/proxy/haproxy.cfg`:

~~~text
global
    log stdout format raw local0

defaults
    log global
    mode http
    option httplog
    timeout connect 5s
    timeout client  50s
    timeout server  50s

frontend http_front
    bind *:80
    default_backend wordpress_backend

backend wordpress_backend
    balance roundrobin
    option httpchk GET /
    server web1 WEB_NODE_PRIVATE_IP:80 check
~~~

`WEB_NODE_PRIVATE_IP`는 실제 Web Node 내부 IP로 변경한다.

---

## 6.3 Proxy Node 검증

~~~bash
docker ps
sudo ss -tulnp | grep ':80'
curl -I http://PROXY_NODE_IP
docker logs dandelion-haproxy --tail 50
~~~

성공 기준:

| 항목 | 기준 |
|---|---|
| Container | dandelion-haproxy running |
| Port | Proxy Node 80 listening |
| Backend | Web Node 80 연결 |
| HTTP | Proxy Node 경유 WordPress 응답 |

---

## 7. Web Node 구성

## 7.1 역할

Web Node는 Custom WordPress 컨테이너를 실행한다.

DB는 Web Node 내부에 두지 않고 DB Node의 MariaDB 서비스에 연결한다.

~~~text
Web Node
→ Custom WordPress Container
→ DB Node MariaDB Service
~~~

---

## 7.2 Custom WordPress Image

권장 경로:

~~~text
docker/wordpress/
├── Dockerfile
├── custom.ini
└── README.md
~~~

예시 `docker/wordpress/Dockerfile`:

~~~dockerfile
FROM wordpress:php8.2-apache

COPY custom.ini /usr/local/etc/php/conf.d/custom.ini

LABEL project="Dandelion"
LABEL service="custom-wordpress"
LABEL base_image="wordpress:php8.2-apache"
LABEL description="Custom WordPress image for Ansible-based cloud infrastructure automation project"
~~~

예시 `docker/wordpress/custom.ini`:

~~~ini
upload_max_filesize=64M
post_max_size=64M
memory_limit=256M
max_execution_time=300
~~~

---

## 7.3 Web Node Docker Compose

권장 경로:

~~~text
docker/compose/web/docker-compose.yml
~~~

예시:

~~~yaml
services:
  wordpress:
    build:
      context: ../../wordpress
      dockerfile: Dockerfile
    container_name: dandelion-wordpress
    restart: unless-stopped
    ports:
      - "80:80"
    environment:
      WORDPRESS_DB_HOST: DB_NODE_PRIVATE_IP:3306
      WORDPRESS_DB_USER: wordpress
      WORDPRESS_DB_PASSWORD: wordpress_password
      WORDPRESS_DB_NAME: wordpress
    volumes:
      - wordpress_data:/var/www/html

volumes:
  wordpress_data:
~~~

`DB_NODE_PRIVATE_IP`는 실제 DB Node 내부 IP로 변경한다.

---

## 7.4 Web Node 검증

~~~bash
docker ps
sudo ss -tulnp | grep ':80'
curl -I http://localhost
curl -I http://WEB_NODE_PRIVATE_IP
nc -zv DB_NODE_PRIVATE_IP 3306
docker logs dandelion-wordpress --tail 50
~~~

성공 기준:

| 항목 | 기준 |
|---|---|
| Container | dandelion-wordpress running |
| Port | Web Node 80 listening |
| DB Connection | WordPress가 DB Node MariaDB 서비스에 연결 |
| HTTP | Web Node 내부 HTTP 응답 |

---

## 8. DB Node 구성

## 8.1 역할

DB Node는 MariaDB를 Ubuntu 패키지로 직접 설치하고 systemd 서비스로 운영한다.

~~~text
DB Node
→ MariaDB Package Install
→ systemctl mariadb
→ WordPress Database
~~~

DB Node의 3306 포트는 전체 공개하지 않고 Web Node와 Backup / Validation Node에서만 접근하도록 제한한다.

---

## 8.2 MariaDB 설치

DB Node에서 MariaDB를 설치한다.

~~~bash
sudo apt update
sudo apt install -y mariadb-server mariadb-client
sudo systemctl enable mariadb
sudo systemctl start mariadb
sudo systemctl status mariadb
~~~

---

## 8.3 MariaDB 외부 접속 설정

WordPress가 Web Node에서 DB Node로 접속해야 하므로 MariaDB bind address를 확인한다.

설정 파일 예시:

~~~bash
sudo grep -R "bind-address" /etc/mysql/mariadb.conf.d/
~~~

필요 시 다음 파일을 수정한다.

~~~bash
sudo vi /etc/mysql/mariadb.conf.d/50-server.cnf
~~~

설정 예시:

~~~ini
bind-address = 0.0.0.0
~~~

수정 후 재시작한다.

~~~bash
sudo systemctl restart mariadb
sudo systemctl status mariadb
~~~

보안그룹에서 3306은 전체 공개하지 않고 Web Node와 Backup / Validation Node만 허용한다.

---

## 8.4 WordPress Database 생성

DB Node에서 WordPress용 DB와 계정을 생성한다.

~~~bash
sudo mariadb
~~~

MariaDB Shell에서 실행한다.

~~~sql
CREATE DATABASE wordpress CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'wordpress'@'%' IDENTIFIED BY 'wordpress_password';
GRANT ALL PRIVILEGES ON wordpress.* TO 'wordpress'@'%';
FLUSH PRIVILEGES;
EXIT;
~~~

실제 비밀번호는 공개 문서나 발표자료에 그대로 노출하지 않는다.

---

## 8.5 DB Node 검증

DB Node에서 확인:

~~~bash
sudo systemctl status mariadb
sudo ss -tulnp | grep ':3306'
sudo mariadb -e "SHOW DATABASES;"
~~~

Web Node에서 DB 연결 확인:

~~~bash
nc -zv DB_NODE_PRIVATE_IP 3306
mysql -h DB_NODE_PRIVATE_IP -u wordpress -p -e "SHOW DATABASES;"
~~~

Backup / Validation Node에서 확인:

~~~bash
nc -zv DB_NODE_PRIVATE_IP 3306
mysqldump -h DB_NODE_PRIVATE_IP -u wordpress -p wordpress > wordpress_db_test.sql
ls -lh wordpress_db_test.sql
~~~

성공 기준:

| 항목 | 기준 |
|---|---|
| Service | mariadb service active |
| Port | DB Node 3306 listening |
| Database | wordpress database 존재 |
| User | wordpress 계정 접속 가능 |
| Access | Web Node에서 DB Node 3306 접근 가능 |
| Backup | mysqldump 실행 가능 |
| Security | DB Node 3306은 전체 공개하지 않음 |

---

## 9. Backup / Validation Node 구성

## 9.1 역할

Backup / Validation Node는 서비스 상태 점검, MariaDB dump, WordPress files archive 생성, 복구 절차 검증을 담당한다.

~~~text
Backup / Validation Node
→ Proxy Node HTTP 확인
→ Web Node WordPress files backup
→ DB Node MariaDB dump
→ restore.md 기반 복구 절차 검증
~~~

---

## 9.2 Backup / Validation Node 필수 패키지

Backup / Validation Node에서 DB dump를 수행하려면 MariaDB client 또는 mysql client가 필요하다.

~~~bash
sudo apt update
sudo apt install -y mariadb-client curl netcat-openbsd tar gzip
~~~

---

## 9.3 상태 점검 기준

`health_check.sh`는 다음 항목을 확인한다.

| 항목 | 확인 대상 |
|---|---|
| Proxy | Proxy Node HTTP 응답 |
| Web | Web Node HTTP 응답 |
| DB | DB Node 3306 연결 |
| Docker | Proxy / Web 컨테이너 running |
| MariaDB | DB Node mariadb service active |
| Disk | df -h |
| Memory | free -h |

예시 실행:

~~~bash
bash scripts/health_check.sh
~~~

---

## 9.4 백업 기준

`backup.sh`는 다음 결과물을 생성해야 한다.

| Backup Target | Output |
|---|---|
| DB Node MariaDB | wordpress_db.sql |
| Web Node WordPress files | wordpress_files.tar.gz |

백업 대상:

~~~text
DB Node
→ MariaDB dump

Web Node
→ WordPress files archive
~~~

예시 저장 경로:

~~~text
backup/
└── YYYYMMDD_HHMMSS/
    ├── wordpress_db.sql
    └── wordpress_files.tar.gz
~~~

---

## 9.5 복구 검증 기준

복구는 `restore.md` 기준으로 절차를 검증한다.

복구 검증은 운영 데이터를 무리하게 덮어쓰는 방식이 아니라, 복구 절차와 명령어가 재현 가능한지 확인하는 것을 우선한다.

DB 복구는 MariaDB 서비스에 dump 파일을 import하는 방식으로 정리한다.

---

## 10. Phase 2 서버 확장

Phase 2에서는 다음 서버 기능을 추가할 수 있다.

| 확장 항목 | 대상 노드 | 설명 |
|---|---|---|
| HTTPS | Proxy Node | self-signed 인증서 기반 HTTPS |
| Redirect | Proxy Node | HTTP 80 → HTTPS 443 |
| Cinder Backup Volume | Backup / Validation Node | /backup 마운트 |
| node_exporter | Proxy / Web / DB Node | OS Metrics |
| cAdvisor | Proxy / Web Node | Container Metrics |
| Prometheus | Monitoring Node | Metrics 수집 |
| Grafana | Monitoring Node | Dashboard 시각화 |
| Ansible roles | Control Node | Playbook 구조 개선 |

---

## 11. Phase 3 서버 확장

Phase 3에서는 Web Node를 2대로 확장할 수 있다.

~~~text
Client
→ Proxy Node / HAProxy Load Balancer
→ Web Node 1 / WordPress
→ Web Node 2 / WordPress
→ DB Node / MariaDB Service
~~~

Phase 3에서 DB Node는 기존 MariaDB 직접 설치 구조를 유지한다.

검증 기준:

| 항목 | 기준 |
|---|---|
| Web Node 2 | WordPress 컨테이너 running |
| HAProxy LB | Web-1 / Web-2 backend 등록 |
| 분산 확인 | roundrobin 응답 분산 |
| 공통 DB | 두 Web Node가 동일 DB Node MariaDB 서비스에 연결 |
| 장애 확인 | Web-1 중지 시 Web-2 응답 |

---

## 12. 제외 기준

다음 항목은 서버 구성 범위에서 제외한다.

~~~text
Kubernetes
Docker Swarm
DB Replication
DB Clustering
WordPress files 자동 동기화
wp-content/uploads 공유
OpenStack LBaaS / Octavia
Production-level HTTPS
실서비스 도메인 및 공인 인증서 자동 갱신
~~~

---

## 13. 필수 캡처 기준

| 영역 | 캡처 항목 |
|---|---|
| OS | cat /etc/os-release |
| Docker | docker --version |
| Docker Compose | docker compose version |
| Proxy Node | dandelion-haproxy running |
| Web Node | dandelion-wordpress running |
| DB Node | systemctl status mariadb |
| DB Node | ss -tulnp 기준 3306 listening |
| DB Node | wordpress database 확인 |
| HTTP | Proxy Node 경유 WordPress 접속 |
| DB | Web Node에서 DB Node 3306 연결 확인 |
| Backup | DB dump 및 WordPress files archive 생성 |
| Restore | restore.md 절차 검증 |

---

## 14. 핵심 서버 구성 메시지

~~~text
본 프로젝트는 WordPress와 MariaDB를 같은 서버에 배치하는 단순 구조가 아니라,
Proxy Node, Web Node, DB Node, Backup / Validation Node를 분리한 기본 운영 구조를 사용한다.

Proxy Node는 HAProxy 컨테이너를 담당하고,
Web Node는 Custom WordPress 컨테이너를 실행하며,
DB Node는 MariaDB를 Ubuntu 패키지로 직접 설치하여 systemd 서비스로 운영한다.

Backup / Validation Node는 상태 점검, mysqldump 기반 백업, 복구 절차 검증을 담당한다.
~~~

<!-- AUTO_IMAGES_START -->
## 자동 반영 이미지

아래 이미지는 screenshots/ 폴더에 파일이 업로드되면 자동으로 표시된다.

### OS Information

../screenshots/server/os-info.png 이미지가 아직 업로드되지 않았다.

### Docker Service Status

../screenshots/server/docker-status.png 이미지가 아직 업로드되지 않았다.

### WordPress/MariaDB Containers Running

../screenshots/server/docker-ps.png 이미지가 아직 업로드되지 않았다.

### HTTP Test Result

../screenshots/server/curl-result.png 이미지가 아직 업로드되지 않았다.
<!-- AUTO_IMAGES_END -->

