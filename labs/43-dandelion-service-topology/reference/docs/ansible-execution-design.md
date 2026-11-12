<!-- STATUS: CURRENT -->

# Ansible Execution Design

## 1. 문서 목적

본 문서는 Team Dandelion 프로젝트의 Ansible 실행 구조를 정의한다.

멘토링 및 최종 발표 시 다음 질문에 답하기 위한 기준 문서이다.

```text
Ansible은 어디서 실행되는가?
어떤 순서로 Playbook이 실행되는가?
현재 완료된 자동화 범위와 보완 예정 범위는 무엇인가?
site.yml은 최종적으로 어떤 구조를 목표로 하는가?
```

---

## 2. 실행 기준

| 항목 | 내용 |
|---|---|
| 실행 위치 | Control Node |
| 실행 도구 | Ansible |
| 대상 환경 | OpenStack 기반 Managed Nodes |
| 대상 노드 | Proxy, Web, DB, Monitoring, Backup / Recovery |
| 최종 목표 | 인스턴스 생성부터 운영 검증까지 Playbook 기반 자동화 |

---

## 3. 최종 실행 목표

최종 목표는 Control Node에서 다음 명령 하나로 전체 자동화 흐름을 실행하는 것이다.

```bash
ansible-playbook -i inventory.ini site.yml
```

목표 실행 흐름은 다음과 같다.

```text
Control Node
→ site.yml 실행
→ OpenStack Provisioning
→ SSH 대기
→ Inventory 확인
→ 공통 환경 설정
→ 서비스 구성
→ 모니터링 구성
→ 백업 구성
→ 복구 및 운영 검증
```

---

## 4. 권장 site.yml 구조

최종 `site.yml`은 다음 구조를 목표로 한다.

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

---

## 5. Playbook별 역할

| Playbook | 역할 | 현재 상태 |
|---|---|---|
| provision.yml | OpenStack 인스턴스, 보안그룹, 볼륨, Floating IP 생성 | 보완 필요 |
| wait-ssh.yml | 생성된 인스턴스 SSH 접속 가능 상태 확인 | 예정 |
| common.yml | 공통 패키지, 시간대, 기본 디렉터리 구성 | 작성 / 검증 대상 |
| docker-swarm.yml | Docker 및 Docker Swarm 기반 Web 구성 | 구조 변경 반영 |
| database.yml | MariaDB 및 Replica 구성 | 진행 / 검증 대상 |
| proxy.yml | HAProxy 구성 | 구성 완료 / 검증 대상 |
| monitoring.yml | Prometheus, Exporter, Grafana, Alertmanager 구성 | 설치 완료 / 설정 진행 |
| backup.yml | Restic 및 백업 스크립트 구성 | Web / DB / Proxy 완료 |
| validate.yml | 서비스, 모니터링, 백업, 복구 검증 | 작성 대상 |

---

## 6. 현재 구현 범위

현재 구현된 자동화 범위는 생성된 인스턴스를 대상으로 한 구성 자동화와 운영 검증 자동화 중심이다.

| 범위 | 내용 |
|---|---|
| Control Node | Ansible 실행 구조 구성 |
| Inventory | 관리 대상 노드 정의 |
| Common | 공통 환경 설정 Playbook 작성 |
| Service | Web / DB / Proxy 구성 Playbook 작성 및 수정 |
| Monitoring | Prometheus / Exporter / Grafana / Alertmanager 설치 구성 |
| Backup | Restic 기반 Web / DB / Proxy 백업 |
| Recovery | 복구 테스트 및 복구 시나리오 구성 |
| Validation | 서비스 상태 및 백업 / 복구 검증 계획 수립 |

---

## 7. 보완 필요 범위

최종 목표 달성을 위해 다음 범위를 추가 보완한다.

| 범위 | 보완 내용 |
|---|---|
| OpenStack Provisioning | Ansible OpenStack 모듈 기반 인스턴스 생성 |
| Security Group | 보안그룹 및 Rule 자동 생성 |
| Volume | Cinder Volume 생성 및 Backup Node attach |
| Floating IP | Control 또는 Proxy 접근용 Floating IP 연결 |
| Inventory | 생성 결과 기반 Inventory 자동 생성 또는 갱신 |
| SSH Wait | 생성된 인스턴스 SSH 준비 상태 대기 |
| Integrated Run | site.yml 통합 실행 |
| Idempotency | 반복 실행 시 안정성 검증 |

---

## 8. 실행 순서 상세

### 8.1 Provisioning 단계

```text
OpenStack 인증 확인
→ Network / Security Group 확인
→ Instance 생성
→ Floating IP 연결
→ Cinder Volume 생성 및 연결
```

### 8.2 SSH 준비 단계

```text
Instance Boot 완료
→ SSH Port Open 확인
→ known_hosts 처리
→ Ansible Ping 확인
```

### 8.3 Common 설정 단계

```text
apt update
→ 공통 패키지 설치
→ timezone KST 설정
→ 공통 디렉터리 생성
```

### 8.4 Service 구성 단계

```text
Docker / Docker Swarm 구성
→ MariaDB 구성
→ HAProxy 구성
→ Web Service 배포
```

### 8.5 Monitoring 구성 단계

```text
Prometheus 설치
→ Exporter 설치
→ Grafana 설치
→ Alertmanager 설치
→ Target 등록
```

### 8.6 Backup / Recovery 단계

```text
Restic 설치
→ Repository 확인
→ Web / DB / Proxy 백업
→ Snapshot 확인
→ Restore Test
```

### 8.7 Validation 단계

```text
Ansible ping
→ Web 응답 확인
→ Proxy 경유 확인
→ DB 접속 확인
→ Prometheus Target 확인
→ Restic Snapshot 확인
→ 복구 결과 확인
```

---

## 9. 멘토링 답변 기준

멘토링에서 “Ansible 기반 자동화가 어디까지 되었는가?”라고 질문받으면 다음 기준으로 답변한다.

```text
현재는 생성된 OpenStack 인스턴스를 대상으로 서버 공통 설정, 서비스 구성, 모니터링, 백업 및 복구 검증 자동화를 구현하고 있습니다.

최종 목표는 Control Node에서 site.yml을 실행하여 OpenStack 인스턴스 생성부터 전체 서비스 구성까지 연결하는 것입니다.

이를 위해 provision.yml, wait-ssh.yml, inventory 갱신 구조를 보완 범위로 분리했고, 현재는 구조 변경에 맞춰 서비스 구성 Playbook과 운영 검증 Playbook을 정리하고 있습니다.
```

---

## 10. 결론

본 프로젝트의 Ansible 실행 구조는 단순 패키지 설치 자동화가 아니라 다음 흐름을 목표로 한다.

```text
Provisioning
→ Configuration
→ Service Deployment
→ Monitoring
→ Backup
→ Recovery Validation
→ Operation Optimization
```

현재는 Configuration / Service / Monitoring / Backup / Recovery 범위를 우선 구현했으며, 최종 목표 달성을 위해 OpenStack Provisioning 자동화를 추가 보완한다.
