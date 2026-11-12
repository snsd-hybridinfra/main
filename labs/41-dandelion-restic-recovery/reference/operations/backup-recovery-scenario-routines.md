# Backup and Recovery Scenario Routines

## 1. 문서 목적

본 문서는 Dandelion 프로젝트의 Restic 기반 백업/복구 검증을 위해 정의한 복구 시나리오별 대응 루틴을 정리한다.

복구 시나리오는 다음 5가지로 구성한다.

1. Web Recovery Scenario
2. Database Recovery Scenario
3. Proxy Recovery Scenario
4. Monitoring Recovery Scenario
5. Backup Recovery Scenario

각 시나리오는 장애 상황, 영향 범위, 백업 대상, 복구 절차, 검증 명령어, 완료 기준으로 구성한다.

---

## 2. 공통 백업/복구 구성

### 2.1 Backup Node 구성

Backup Node에는 Cinder Volume을 `/backup` 경로로 마운트하고, Restic Repository를 `/backup/restic-repo`에 구성하였다.

~~~text
/backup
├── restic-repo
├── restic-cache
├── staging
│   ├── db
│   ├── wordpress
│   ├── haproxy
│   ├── prometheus
│   └── evidence
├── logs
├── scripts
└── restore-test
~~~

### 2.2 Restic 환경 파일

Restic 환경 파일은 다음 경로에 구성한다.

~~~text
/etc/restic/restic.env
/etc/restic/restic-password
~~~

환경 변수 예시는 다음과 같다.

~~~bash
export RESTIC_REPOSITORY=/backup/restic-repo
export RESTIC_PASSWORD_FILE=/etc/restic/restic-password
export RESTIC_CACHE_DIR=/backup/restic-cache
~~~

### 2.3 공통 복구 명령어

각 시나리오에서 Restic snapshot을 복구할 때 공통적으로 다음 명령어를 사용한다.

~~~bash
sudo rm -rf /backup/restore-test/*

sudo bash -c 'source /etc/restic/restic.env && restic restore latest --target /backup/restore-test'
~~~

Restic snapshot 조회는 다음 명령어로 수행한다.

~~~bash
sudo bash -c 'source /etc/restic/restic.env && restic snapshots'
~~~

Restic repository 무결성 검사는 다음 명령어로 수행한다.

~~~bash
sudo bash -c 'source /etc/restic/restic.env && restic check'
~~~

---

# Scenario 1. Web Recovery Scenario

## 1. 장애 상황

Docker Swarm 기반 WordPress replica 또는 WordPress volume이 손상되어 Web 서비스 파일이 유실된 상황을 가정한다.

## 2. 영향 범위

- WordPress 컨테이너 파일 손상
- WordPress 업로드 파일 또는 플러그인 파일 유실 가능
- Proxy를 통한 웹 서비스 접속 실패 또는 비정상 응답
- replica별 local volume 불일치 가능성 존재

## 3. 백업 대상

Docker Swarm 기반 WordPress 서비스는 replica별 local volume이 `/var/www/html`에 마운트되는 구조로 확인되었다.

백업 대상은 다음과 같다.

~~~text
/backup/staging/wordpress/wordpress-replica-1-volume.tar.gz
/backup/staging/wordpress/wordpress-replica-2-volume.tar.gz
~~~

## 4. 복구 절차

Restic 최신 snapshot을 `/backup/restore-test` 경로에 복구한다.

~~~bash
sudo rm -rf /backup/restore-test/*

sudo bash -c 'source /etc/restic/restic.env && restic restore latest --target /backup/restore-test'
~~~

복구된 WordPress archive 파일을 확인한다.

~~~bash
ls -lh /backup/restore-test/backup/staging/wordpress/
~~~

복구 테스트용 디렉터리를 생성한다.

~~~bash
mkdir -p /tmp/wordpress-recovery-test/replica-1
mkdir -p /tmp/wordpress-recovery-test/replica-2
~~~

replica별 WordPress volume archive를 압축 해제한다.

~~~bash
tar -xzf /backup/restore-test/backup/staging/wordpress/wordpress-replica-1-volume.tar.gz -C /tmp/wordpress-recovery-test/replica-1

tar -xzf /backup/restore-test/backup/staging/wordpress/wordpress-replica-2-volume.tar.gz -C /tmp/wordpress-recovery-test/replica-2
~~~

## 5. 검증 명령어

archive 내부 파일 목록을 확인한다.

~~~bash
for f in /backup/restore-test/backup/staging/wordpress/*.tar.gz; do
  echo "===== $f ====="
  tar -tzf "$f" | head -n 20
done
~~~

압축 해제된 WordPress 파일 구조를 확인한다.

~~~bash
find /tmp/wordpress-recovery-test -maxdepth 3 -type f | head
~~~

## 6. 완료 기준

다음 조건을 만족하면 Web Recovery 성공으로 판단한다.

- Restic restore를 통해 WordPress replica별 archive가 복구됨
- `wordpress-replica-1-volume.tar.gz` 확인 가능
- `wordpress-replica-2-volume.tar.gz` 확인 가능
- tar 내부 파일 목록 확인 가능
- 압축 해제 후 WordPress 파일 구조 확인 가능

---

# Scenario 2. Database Recovery Scenario

## 1. 장애 상황

MariaDB Primary DB의 `wordpress_db` 데이터가 손상되거나 유실된 상황을 가정한다.

## 2. 영향 범위

- WordPress 게시글, 사용자, 설정 데이터 손상
- WordPress 서비스 접속은 가능하더라도 콘텐츠 조회 실패 가능
- DB 연결 오류 또는 테이블 손상 발생 가능

## 3. 백업 대상

MariaDB Primary DB에서 `wordpress_db`를 dump 파일로 백업한다.

백업 대상은 다음과 같다.

~~~text
/backup/staging/db/wordpress_db-primary.sql
~~~

## 4. 복구 절차

Restic 최신 snapshot을 `/backup/restore-test` 경로에 복구한다.

~~~bash
sudo rm -rf /backup/restore-test/*

sudo bash -c 'source /etc/restic/restic.env && restic restore latest --target /backup/restore-test'
~~~

복구된 DB dump 파일을 확인한다.

~~~bash
ls -lh /backup/restore-test/backup/staging/db/
head -n 20 /backup/restore-test/backup/staging/db/wordpress_db-primary.sql
~~~

DB Node로 dump 파일을 전송한다.

~~~bash
scp /backup/restore-test/backup/staging/db/wordpress_db-primary.sql db_primary:/tmp/
~~~

DB Node에서 dump 파일을 import한다.

~~~bash
ssh db_primary 'sudo mysql wordpress_db < /tmp/wordpress_db-primary.sql'
~~~

## 5. 검증 명령어

DB 목록을 확인한다.

~~~bash
ssh db_primary 'sudo mysql -e "SHOW DATABASES;"'
~~~

WordPress DB의 테이블을 확인한다.

~~~bash
ssh db_primary 'sudo mysql -e "USE wordpress_db; SHOW TABLES;"'
~~~

WordPress 핵심 테이블을 확인한다.

~~~bash
ssh db_primary 'sudo mysql -e "USE wordpress_db; SHOW TABLES LIKE '\''wp_%'\'';"'
~~~

## 6. 완료 기준

다음 조건을 만족하면 Database Recovery 성공으로 판단한다.

- Restic restore를 통해 DB dump 파일이 복구됨
- `wordpress_db-primary.sql` 파일 확인 가능
- DB import 명령어 실행 가능
- `wordpress_db` 내 WordPress 테이블 조회 가능

---

# Scenario 3. Proxy Recovery Scenario

## 1. 장애 상황

Proxy Node의 HAProxy 설정 파일이 손상되거나 삭제되어 사용자가 WordPress 서비스에 접근하지 못하는 상황을 가정한다.

## 2. 영향 범위

- 외부 사용자의 WordPress 서비스 접근 실패
- Web Node는 정상이어도 Proxy 경유 트래픽 전달 실패
- Reverse Proxy 설정 손상으로 HTTP 응답 실패 가능

## 3. 백업 대상

Proxy Node의 HAProxy 설정 디렉터리를 archive 형태로 백업한다.

백업 대상은 다음과 같다.

~~~text
/backup/staging/haproxy/haproxy-config.tar.gz
~~~

## 4. 복구 절차

Restic 최신 snapshot을 `/backup/restore-test` 경로에 복구한다.

~~~bash
sudo rm -rf /backup/restore-test/*

sudo bash -c 'source /etc/restic/restic.env && restic restore latest --target /backup/restore-test'
~~~

복구된 HAProxy archive 파일을 확인한다.

~~~bash
ls -lh /backup/restore-test/backup/staging/haproxy/
tar -tzf /backup/restore-test/backup/staging/haproxy/haproxy-config.tar.gz | head
~~~

Proxy Node로 HAProxy archive 파일을 전송한다.

~~~bash
scp /backup/restore-test/backup/staging/haproxy/haproxy-config.tar.gz proxy:/tmp/
~~~

Proxy Node에서 `/etc` 경로 기준으로 압축을 해제한다.

~~~bash
ssh proxy 'sudo tar -xzf /tmp/haproxy-config.tar.gz -C /etc'
~~~

HAProxy 설정 문법을 검사한다.

~~~bash
ssh proxy 'sudo haproxy -c -f /etc/haproxy/haproxy.cfg'
~~~

HAProxy 서비스를 재시작한다.

~~~bash
ssh proxy 'sudo systemctl restart haproxy'
~~~

## 5. 검증 명령어

HAProxy 서비스 상태를 확인한다.

~~~bash
ssh proxy 'sudo systemctl status haproxy --no-pager'
~~~

Proxy Node HTTP 응답을 확인한다.

~~~bash
curl -I http://<synthetic-private-ip>
~~~

## 6. 완료 기준

다음 조건을 만족하면 Proxy Recovery 성공으로 판단한다.

- Restic restore를 통해 HAProxy 설정 archive가 복구됨
- `haproxy-config.tar.gz` 내부 파일 확인 가능
- HAProxy 설정 검사 통과
- HAProxy 서비스 재시작 성공
- Proxy Node를 통한 HTTP 응답 확인 가능

---

# Scenario 4. Monitoring Recovery Scenario

## 1. 장애 상황

Monitoring Node 또는 Prometheus 설정 손상으로 인해 모니터링 대상 수집이 불가능한 상황을 가정한다.

## 2. 영향 범위

- Node Exporter, cAdvisor, mysqld_exporter, blackbox_exporter 수집 상태 확인 불가
- 장애 탐지 및 운영 가시성 저하
- Grafana Dashboard 및 Prometheus Target 상태 확인 불가

## 3. 현재 상태

현재 Prometheus 실제 설정은 완료 전 단계이며, `/backup/staging/prometheus/README.md` placeholder만 백업 대상으로 구성하였다.

현재 백업 대상은 다음과 같다.

~~~text
/backup/staging/prometheus/README.md
~~~

향후 Prometheus 구성 완료 후 백업 대상은 다음 항목으로 확장한다.

~~~text
/etc/prometheus/prometheus.yml
/etc/prometheus/rules/
/etc/prometheus/targets/
blackbox exporter config
node exporter target list
mysqld exporter target
~~~

## 4. 복구 절차

현재 단계에서는 Prometheus placeholder 복구를 검증한다.

~~~bash
sudo rm -rf /backup/restore-test/*

sudo bash -c 'source /etc/restic/restic.env && restic restore latest --target /backup/restore-test'
~~~

복구된 placeholder 파일을 확인한다.

~~~bash
cat /backup/restore-test/backup/staging/prometheus/README.md
~~~

향후 실제 Prometheus 설정 파일이 백업 대상에 포함되면 다음 절차를 수행한다.

~~~bash
scp /backup/restore-test/backup/staging/prometheus/prometheus.yml monitoring:/tmp/

ssh monitoring 'sudo cp /tmp/prometheus.yml /etc/prometheus/prometheus.yml'
ssh monitoring 'sudo promtool check config /etc/prometheus/prometheus.yml'
ssh monitoring 'sudo systemctl restart prometheus'
~~~

## 5. 검증 명령어

현재 단계의 검증 명령어는 다음과 같다.

~~~bash
cat /backup/restore-test/backup/staging/prometheus/README.md
~~~

향후 Prometheus 구성 완료 후 검증 명령어는 다음과 같다.

~~~bash
ssh monitoring 'sudo systemctl status prometheus --no-pager'
ssh monitoring 'curl -s http://localhost:9090/-/ready'
ssh monitoring 'curl -s http://localhost:9090/api/v1/targets'
~~~

## 6. 완료 기준

현재 단계에서는 다음 조건을 만족하면 Monitoring Recovery 사전 루틴 검증 완료로 판단한다.

- Restic restore를 통해 Prometheus placeholder가 복구됨
- `/backup/restore-test/backup/staging/prometheus/README.md` 확인 가능

향후 Prometheus 구성이 완료되면 다음 조건을 추가 완료 기준으로 적용한다.

- `prometheus.yml` 복구 가능
- `promtool check config` 통과
- Prometheus 서비스 재시작 성공
- Prometheus target 상태 확인 가능

---

# Scenario 5. Backup Recovery Scenario

## 1. 장애 상황

Backup Node의 staging 데이터 손상, restore-test 검증 필요, 또는 Restic snapshot 기반 복구 가능성 확인이 필요한 상황을 가정한다.

## 2. 영향 범위

- 백업 대상 파일 직접 접근 불가
- 장애 발생 시 Web, DB, Proxy 복구 지연 가능
- Restic Repository 무결성 문제 발생 시 복구 실패 가능

## 3. 백업 대상

Backup Recovery는 특정 서비스 하나가 아니라 전체 백업 대상과 Restic Repository 상태를 검증한다.

검증 대상은 다음과 같다.

~~~text
/backup/staging/db
/backup/staging/wordpress
/backup/staging/haproxy
/backup/staging/prometheus
/backup/staging/evidence
/backup/restic-repo
~~~

## 4. 복구 절차

Restic snapshot을 조회한다.

~~~bash
sudo bash -c 'source /etc/restic/restic.env && restic snapshots'
~~~

Restic repository 무결성을 검사한다.

~~~bash
sudo bash -c 'source /etc/restic/restic.env && restic check'
~~~

최신 snapshot을 `/backup/restore-test` 경로에 복구한다.

~~~bash
sudo rm -rf /backup/restore-test/*

sudo bash -c 'source /etc/restic/restic.env && restic restore latest --target /backup/restore-test'
~~~

복구 결과 파일 목록을 확인한다.

~~~bash
find /backup/restore-test -maxdepth 6 -type f | sort
~~~

## 5. 검증 명령어

복구된 서비스별 백업 파일을 확인한다.

~~~bash
ls -lh /backup/restore-test/backup/staging/db/
ls -lh /backup/restore-test/backup/staging/wordpress/
ls -lh /backup/restore-test/backup/staging/haproxy/
ls -lh /backup/restore-test/backup/staging/prometheus/
ls -lh /backup/restore-test/backup/staging/evidence/
~~~

Restic repository 상태를 재확인한다.

~~~bash
sudo bash -c 'source /etc/restic/restic.env && restic check'
~~~

## 6. 완료 기준

다음 조건을 만족하면 Backup Recovery 검증 성공으로 판단한다.

- Restic snapshot 조회 성공
- Restic repository check 성공
- 최신 snapshot restore 성공
- `/backup/restore-test` 경로에 서비스별 백업 파일 복구 확인
- DB, WordPress, HAProxy, Prometheus, Evidence 백업 파일 확인 가능

---

## 3. 최종 검증 결과 요약

본 프로젝트에서는 Restic 기반 백업/복구 검증을 위해 Web, Database, Proxy, Monitoring, Backup 관점의 5가지 복구 시나리오를 정의하였다.

실제 구성 및 검증 완료 항목은 다음과 같다.

| 구분 | 백업 대상 | 검증 상태 |
|---|---|---|
| Web | Docker Swarm WordPress replica volume | 완료 |
| Database | MariaDB wordpress_db dump | 완료 |
| Proxy | HAProxy 설정 archive | 완료 |
| Monitoring | Prometheus placeholder | 준비 완료 |
| Backup | Restic snapshot, repository check, restore-test | 완료 |

Monitoring 항목은 Prometheus 실제 구성이 완료되기 전 단계이므로, 현재는 백업 예정 경로와 README placeholder 복구를 기준으로 사전 루틴을 정의하였다.

---

## 4. 보고서 작성용 요약 문구

Backup Node에 연결된 Cinder Volume을 `/backup` 경로로 마운트하고 Restic Repository를 `/backup/restic-repo`에 구성하였다. 이후 Docker Swarm 기반 WordPress replica volume, MariaDB `wordpress_db` dump, HAProxy 설정 파일, Prometheus 백업 예정 경로, evidence 파일을 `/backup/staging` 경로에 수집하였다.

수집된 백업 대상은 Restic을 통해 `automated-backup` 태그로 백업하였으며, `restic snapshots` 조회와 `restic check`를 통해 snapshot 생성 및 repository 무결성을 확인하였다. 또한 latest snapshot을 `/backup/restore-test` 경로에 복구하여 WordPress, DB, HAProxy, Prometheus placeholder, evidence 파일이 정상 복구되는 것을 검증하였다.

백업 스크립트는 root crontab에 등록하여 매일 02:00에 자동 실행되도록 구성하였다.

