<!-- STATUS: CURRENT -->

# Validation Plan

## 1. 문서 목적

본 문서는 Team Dandelion 프로젝트의 검증 계획을 정리한다.

검증 대상은 다음과 같다.

```text
Infrastructure
Ansible
Web
Proxy
DB
Monitoring
Backup
Recovery
Documentation
```

---

## 2. 검증 원칙

검증은 단순 설치 여부가 아니라 운영 가능한 상태를 기준으로 한다.

| 기준 | 설명 |
|---|---|
| 연결성 | Control Node에서 대상 노드 접근 가능 |
| 구성 일관성 | 문서, Inventory, 실제 인스턴스 구조 일치 |
| 서비스 상태 | 주요 서비스 active 상태 |
| 응답성 | 사용자 요청에 대한 HTTP / DB / Monitoring 응답 |
| 자동화 가능성 | Playbook 반복 실행 가능 |
| 백업 가능성 | 백업 snapshot 생성 |
| 복구 가능성 | 복구 테스트 결과 확인 |
| 증빙 가능성 | 캡처 / 로그 / 문서로 결과 제시 가능 |

---

## 3. Infrastructure 검증

| 검증 항목 | 방법 | 성공 기준 |
|---|---|---|
| 인스턴스 상태 | OpenStack Console 확인 | 모든 노드 Active |
| IP 구성 | `ip addr`, OpenStack IP 확인 | 문서와 실제 IP 일치 |
| Security Group | OpenStack Security Group 확인 | 필요한 포트 허용 |
| Cinder Volume | `lsblk`, `df -h` | Backup Volume 마운트 확인 |
| 시간대 | `timedatectl` | Asia/Seoul 또는 KST 기준 |

---

## 4. Ansible 검증

| 검증 항목 | 명령 | 성공 기준 |
|---|---|---|
| Inventory 확인 | `ansible-inventory -i inventory.ini --list` | 그룹 / 호스트 정상 출력 |
| Ping 확인 | `ansible all -i inventory.ini -m ping` | 전체 pong |
| Syntax Check | `ansible-playbook -i inventory.ini <playbook>.yml --syntax-check` | 에러 없음 |
| Playbook 실행 | `ansible-playbook -i inventory.ini <playbook>.yml` | failed=0 |
| 멱등성 | 동일 Playbook 2회 실행 | changed 감소 또는 안정화 |

---

## 5. Web 검증

| 검증 항목 | 명령 / 방법 | 성공 기준 |
|---|---|---|
| Docker 상태 | `docker ps` | Web 컨테이너 실행 |
| Swarm 상태 | `docker node ls`, `docker service ls` | Service Running |
| Web 응답 | `curl http://<web-or-proxy-ip>` | HTTP 200 또는 정상 응답 |
| WordPress 접근 | Browser / curl | WordPress 화면 확인 |
| 서비스 로그 | `docker logs` | 치명적 오류 없음 |

---

## 6. Proxy / HAProxy 검증

| 검증 항목 | 명령 / 방법 | 성공 기준 |
|---|---|---|
| HAProxy 상태 | `systemctl status haproxy` | active |
| 설정 문법 | `haproxy -c -f /etc/haproxy/haproxy.cfg` | Configuration file is valid |
| Proxy 응답 | `curl http://<proxy-ip>` | Web 서비스 응답 |
| 포트 확인 | `ss -lntp` | 80 / 443 Listen |

---

## 7. DB 검증

| 검증 항목 | 명령 / 방법 | 성공 기준 |
|---|---|---|
| MariaDB 상태 | `systemctl status mariadb` | active |
| DB 접속 | `mysql -u <user> -p` | 접속 성공 |
| WordPress DB 연동 | Web 화면 / 로그 확인 | DB 연결 오류 없음 |
| Replica 상태 | `SHOW REPLICA STATUS\G` 또는 구성 기준 명령 | 복제 상태 확인 |
| DB 백업 | mysqldump 또는 Restic 백업 결과 | 백업 파일 / snapshot 생성 |

---

## 8. Monitoring 검증

| 검증 항목 | 방법 | 성공 기준 |
|---|---|---|
| Prometheus | Web UI 접속 | 접속 가능 |
| node_exporter | Prometheus Target | UP |
| cAdvisor | Prometheus Target | UP |
| mysqld_exporter | Prometheus Target | UP |
| blackbox_exporter | Prometheus Target | UP |
| Grafana | Web UI 접속 | 접속 가능 |
| Data Source | Grafana 설정 | Prometheus 연결 성공 |
| Alertmanager | Web UI 접속 | 접속 가능 |
| Alert Rule | 테스트 Rule | 상태 확인 |

---

## 9. Backup 검증

| 검증 항목 | 명령 / 방법 | 성공 기준 |
|---|---|---|
| Restic 설치 | `restic version` | 버전 출력 |
| Repository 확인 | `restic snapshots` | snapshot 목록 출력 |
| Web 백업 | 백업 스크립트 실행 | snapshot 생성 |
| DB 백업 | 백업 스크립트 실행 | DB dump 또는 snapshot 생성 |
| Proxy 백업 | 백업 스크립트 실행 | 설정 파일 백업 |
| Monitoring 백업 | Monitoring 완료 후 추가 | 예정 |

---

## 10. Recovery 검증

복구 시나리오는 5종으로 구성한다.

| 번호 | 시나리오 | 검증 내용 |
|---:|---|---|
| 1 | Web Service 복구 | Web 파일 / 컨테이너 / 서비스 복구 |
| 2 | DB 복구 | DB dump 또는 snapshot 기반 복구 |
| 3 | Proxy 복구 | HAProxy 설정 복구 |
| 4 | Backup Repository 검증 | Restic snapshot 조회 및 무결성 확인 |
| 5 | 복합 장애 복구 | Web / DB / Proxy 중 복합 장애 대응 절차 확인 |

---

## 11. 검증 결과 기록 방식

검증 결과는 다음 형식으로 기록한다.

| 항목 | 내용 |
|---|---|
| 검증 일자 | YYYY-MM-DD |
| 검증자 | 담당자 |
| 대상 | Web / DB / Proxy / Monitoring / Backup |
| 명령 | 실행 명령 |
| 결과 | 성공 / 실패 |
| 증빙 | 캡처 파일명 또는 로그 |
| 후속 조치 | 필요 시 보완 사항 |

---

## 12. 멘토링 설명 기준

```text
검증은 단순 설치 확인이 아니라 실제 운영 가능한 상태 확인을 기준으로 진행합니다.

서비스 응답, Prometheus target, Restic snapshot, 복구 테스트 결과를 통해 구성 자동화와 운영 검증이 연결되어 있음을 보여주는 것이 목표입니다.
```
