<!-- STATUS: CURRENT -->

# Automation Scope

## 1. 문서 목적

본 문서는 Team Dandelion 프로젝트의 자동화 범위를 명확히 구분하기 위한 문서이다.

프로젝트의 최종 목표는 Control Node에서 Ansible Playbook을 실행하여 OpenStack 인스턴스 생성부터 서비스 구성, 모니터링, 백업 및 복구 검증까지 자동화하는 것이다.

다만 현재 구현 상태에서는 인스턴스 생성 자동화와 생성 이후 구성 자동화의 진행 수준이 다르므로, 완료 / 진행 중 / 예정 범위를 분리하여 정리한다.

---

## 2. 자동화 목표

```text
Control Node
→ Ansible Playbook 실행
→ OpenStack 인스턴스 생성
→ 네트워크 / 보안그룹 / 볼륨 구성
→ SSH 접속 가능 상태 확인
→ Inventory 구성
→ 공통 환경 설정
→ 서비스 구성
→ 모니터링 구성
→ 백업 및 복구 검증
```

---

## 3. 자동화 범위 구분

| 구분 | 설명 | 현재 상태 |
|---|---|---|
| Provisioning Automation | OpenStack 인스턴스, 네트워크, 보안그룹, 볼륨 생성 자동화 | 보완 필요 |
| Configuration Automation | 생성된 서버의 공통 설정, 패키지 설치, 서비스 구성 자동화 | 진행 / 일부 완료 |
| Service Deployment Automation | Web, DB, Proxy 서비스 배포 자동화 | 진행 / 구조 변경 반영 중 |
| Monitoring Automation | Prometheus, Exporter, Grafana, Alertmanager 구성 자동화 | 설치 완료 / 설정 진행 |
| Backup Automation | Restic 기반 백업 구성 및 스크립트 자동화 | Web / DB / Proxy 완료 |
| Recovery Validation | 복구 시나리오 기반 복구 테스트 및 문서화 | 테스트 실시 / 문서 작성 중 |
| Operation Validation | 상태 점검, 서비스 검증, 장애 대응 체크리스트 | 진행 중 |

---

## 4. 현재 완료된 자동화 및 구성 범위

| 영역 | 완료 내용 |
|---|---|
| Control Node | Ansible 실행 구조 구성 |
| Inventory | 관리 대상 노드 정의 |
| Common Setup | 공통 패키지 및 기본 환경 설정 Playbook 작성 |
| Web | Docker Swarm 기반 Web 구성 반영 |
| Proxy | HAProxy 구성 |
| Monitoring | Prometheus 및 주요 Exporter 설치 |
| Monitoring | Grafana 및 Alertmanager 설치 |
| Backup | Restic 설치 |
| Backup | Web / DB / Proxy Node 백업 수행 |
| Recovery | 백업 데이터 기반 복구 테스트 실시 |
| Scenario | 복구 시나리오 5종 구성 |

---

## 5. 진행 중인 자동화 범위

| 영역 | 진행 중인 작업 |
|---|---|
| OpenStack Provisioning | 인스턴스 생성 자동화 Playbook 보완 |
| OpenStack Provisioning | Security Group / Volume / Floating IP 자동화 검토 |
| Ansible | Docker Swarm 구조 변경 대응 Playbook 수정 |
| Ansible | HAProxy 구성 변경 대응 Playbook 수정 |
| Ansible | Monitoring 구성 반영 Playbook 수정 |
| DB | MariaDB Replica 이중화 검증 |
| Monitoring | Grafana Dashboard 설정 |
| Monitoring | Alertmanager 알림 설정 |
| Backup | Monitoring 파트 백업 항목 추가 |
| Recovery | 복구 시나리오 문서화 |
| Validation | 전체 검증 체크리스트 작성 |

---

## 6. 예정 자동화 범위

| 영역 | 예정 작업 |
|---|---|
| Provisioning | `provision.yml` 작성 |
| Provisioning | OpenStack 인스턴스 생성 |
| Provisioning | Security Group 생성 및 Rule 적용 |
| Provisioning | Cinder Volume 생성 및 Attach |
| Provisioning | Floating IP 연결 |
| Inventory | 생성 결과 기반 Inventory 자동 생성 또는 갱신 |
| Integration | `site.yml` 통합 실행 순서 정리 |
| Validation | 전체 Playbook 순차 실행 |
| Validation | 멱등성 검증 |
| Documentation | 실행 결과 및 실패 대응 절차 문서화 |

---

## 7. 권장 Playbook 구조

최종 자동화 구조는 다음과 같이 정리한다.

```text
site.yml
├── provision.yml
├── wait-ssh.yml
├── common.yml
├── docker-swarm.yml
├── database.yml
├── proxy.yml
├── monitoring.yml
├── backup.yml
└── validate.yml
```

### 7.1 provision.yml

OpenStack 리소스를 생성한다.

```text
- Network / Subnet 확인 또는 생성
- Security Group 생성
- Security Group Rule 생성
- Instance 생성
- Floating IP 연결
- Cinder Volume 생성
- Volume Attach
```

### 7.2 wait-ssh.yml

생성된 인스턴스에 SSH 접속 가능한지 확인한다.

```text
- SSH Port 대기
- Host Key 처리
- Inventory 갱신 또는 확인
```

### 7.3 common.yml

모든 관리 노드의 공통 환경을 구성한다.

```text
- apt update
- 기본 패키지 설치
- timezone 설정
- 공통 디렉터리 생성
```

### 7.4 docker-swarm.yml

Web Node의 Docker Swarm 기반 서비스 구성을 반영한다.

```text
- Docker 설치
- Swarm 초기화
- WordPress Service 배포
- 서비스 상태 확인
```

### 7.5 database.yml

DB Node를 구성한다.

```text
- MariaDB 설치
- DB 생성
- 계정 생성
- Replica 구성 및 검증
```

### 7.6 proxy.yml

Proxy / HAProxy 구성을 반영한다.

```text
- HAProxy 설치
- 설정 파일 배포
- 서비스 시작
- HTTP 응답 확인
```

### 7.7 monitoring.yml

Monitoring Stack을 구성한다.

```text
- Prometheus
- node_exporter
- cAdvisor
- mysqld_exporter
- blackbox_exporter
- Grafana
- Alertmanager
```

### 7.8 backup.yml

Restic 기반 백업을 구성한다.

```text
- Restic 설치
- Repository 초기화
- Web / DB / Proxy 백업
- Monitoring 백업 추가 예정
```

### 7.9 validate.yml

운영 검증을 수행한다.

```text
- Ansible ping
- Web 서비스 응답
- Proxy 경유 응답
- DB 상태
- Prometheus target
- Backup snapshot
- Restore test result
```

---

## 8. 멘토링 답변 기준

멘토링에서 “인스턴스 생성부터 자동화가 되었는가?”라는 질문이 나올 경우 다음 기준으로 답변한다.

```text
현재는 생성된 OpenStack 인스턴스 기반의 서비스 구성, 모니터링, 백업 및 복구 검증 자동화를 우선 구현했습니다.

최종 목표는 Control Node에서 Ansible Playbook을 실행하여 인스턴스 생성부터 전체 서비스 구성까지 자동화하는 것이며, 이를 위해 OpenStack Provisioning Playbook을 추가 구현 범위로 분리했습니다.

즉 현재 프로젝트는 Configuration / Operation / Recovery 자동화는 상당 부분 구현되었고, Provisioning 자동화는 최종 목표 달성을 위한 보완 단계입니다.
```

---

## 9. 자동화 범위 결론

본 프로젝트의 자동화 범위는 단순 패키지 설치 자동화가 아니다.

최종적으로 다음 흐름을 목표로 한다.

```text
Provisioning Automation
→ Configuration Automation
→ Service Deployment Automation
→ Monitoring Automation
→ Backup Automation
→ Recovery Validation
→ Operation Optimization
```

현재는 중간 단계인 Configuration / Service / Monitoring / Backup / Recovery 자동화 구현이 진행되었으며, 최종 완성을 위해 Provisioning Automation을 보완한다.
