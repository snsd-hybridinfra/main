<!-- STATUS: CURRENT -->

# Monitoring Plan

## 1. 문서 목적

본 문서는 Team Dandelion 프로젝트의 Monitoring 구성 계획과 검증 기준을 정리한다.

Monitoring Stack은 Prometheus, Exporter, Grafana, Alertmanager를 기준으로 구성한다.

---

## 2. Monitoring 목표

```text
Web, DB, Proxy, Host, Container 상태를 수집하고,
Grafana를 통해 시각화하며,
Alertmanager를 통해 장애 알림 구조를 구성한다.
```

---

## 3. Monitoring 구성 요소

| 구성 요소 | 역할 | 상태 |
|---|---|---|
| Prometheus | 메트릭 수집 및 저장 | 설치 완료 |
| node_exporter | Host OS 메트릭 수집 | 설치 완료 |
| cAdvisor | Container 메트릭 수집 | 설치 완료 |
| mysqld_exporter | MariaDB 메트릭 수집 | 설치 완료 |
| blackbox_exporter | HTTP / Endpoint 상태 점검 | 설치 완료 |
| Grafana | Dashboard 시각화 | 설치 완료 / 설정 진행 |
| Alertmanager | 알림 관리 | 설치 완료 / 설정 진행 |

---

## 4. 수집 대상

| 대상 | 수집 항목 |
|---|---|
| Host | CPU, Memory, Disk, Network |
| Web / Container | Container CPU, Memory, 상태, 재시작 |
| DB | MariaDB 상태, 연결 수, 쿼리 관련 메트릭 |
| Proxy / HTTP | HTTP Endpoint 응답 상태 |
| Backup | 백업 성공 여부, snapshot 확인 결과 |
| Recovery | 복구 테스트 결과, 문서화 상태 |

---

## 5. Exporter별 역할

### 5.1 node_exporter

Host OS 상태를 수집한다.

```text
CPU
Memory
Disk
Network
Filesystem
Load Average
```

### 5.2 cAdvisor

Docker / Container 상태를 수집한다.

```text
Container CPU
Container Memory
Container Network
Container Restart
Container Running State
```

### 5.3 mysqld_exporter

MariaDB 상태를 수집한다.

```text
Connection
Query
Replication
Buffer
Table
Status Variables
```

### 5.4 blackbox_exporter

서비스 Endpoint 상태를 점검한다.

```text
HTTP 응답
TCP 연결
Endpoint Availability
Response Time
```

---

## 6. Prometheus Target 검증

Prometheus Target에서 다음 항목을 확인한다.

| Target | 성공 기준 |
|---|---|
| node_exporter | UP |
| cAdvisor | UP |
| mysqld_exporter | UP |
| blackbox_exporter | UP |
| Prometheus 자체 | UP |

---

## 7. Grafana 구성 계획

Grafana에서는 다음 Dashboard를 구성한다.

| Dashboard | 내용 |
|---|---|
| Host Overview | CPU, Memory, Disk, Network |
| Container Overview | Docker / Swarm / Container 상태 |
| Database Overview | MariaDB 주요 메트릭 |
| Service Availability | HTTP Endpoint 상태 |
| Backup / Recovery Status | 백업 및 복구 검증 결과 요약 |

현재 Grafana는 설치 완료 상태이며, Data Source와 Dashboard 세부 설정을 진행 중이다.

---

## 8. Alertmanager 구성 계획

Alertmanager는 다음 장애 상황을 기준으로 설정한다.

| Alert | 조건 |
|---|---|
| Host Down | node_exporter target down |
| Web Endpoint Down | blackbox_exporter HTTP check fail |
| DB Down | mysqld_exporter target down |
| Disk Usage High | Disk usage threshold 초과 |
| Container Down | cAdvisor 기준 컨테이너 상태 이상 |
| Backup Failure | 백업 결과 실패 또는 snapshot 미생성 |

현재 Alertmanager는 설치 완료 상태이며, 알림 정책과 Receiver 설정을 진행 중이다.

---

## 9. Monitoring 검증 절차

```text
1. Prometheus 접속
2. Target 상태 확인
3. node_exporter UP 확인
4. cAdvisor UP 확인
5. mysqld_exporter UP 확인
6. blackbox_exporter UP 확인
7. Grafana Data Source 연결 확인
8. Dashboard 표시 확인
9. Alertmanager 접속 확인
10. 테스트 Alert Rule 확인
```

---

## 10. Backup / Recovery 연계

Monitoring 파트의 백업은 다음 항목을 대상으로 한다.

| 대상 | 백업 내용 | 상태 |
|---|---|---|
| Prometheus | prometheus.yml, rules, data 보존 정책 | 예정 |
| Grafana | dashboard, datasource, provisioning config | 예정 |
| Alertmanager | alertmanager.yml | 예정 |
| Exporter 설정 | service unit, config file | 예정 |

Monitoring 파트 작업 완료 후 Restic 백업 스크립트에 해당 항목을 추가한다.

---

## 11. 멘토링 설명 기준

```text
Monitoring은 Prometheus와 Exporter 기반으로 Host, Container, DB, Endpoint 상태를 수집하는 구조입니다.

Grafana와 Alertmanager는 설치 완료 후 세부 설정을 진행 중입니다.

최종적으로 Prometheus target up, Grafana Dashboard, Alertmanager Rule, Backup / Recovery 연계를 통해 운영 최적화 구조를 보여주는 것이 목표입니다.
```
