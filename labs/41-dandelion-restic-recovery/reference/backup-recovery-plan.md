<!-- STATUS: CURRENT -->

# Backup and Recovery Plan

## 1. 문서 목적

본 문서는 Team Dandelion 프로젝트의 백업 및 복구 계획을 정리한다.

백업 및 복구는 Restic을 기준으로 구성하며, Web / DB / Proxy Node 백업과 복구 테스트를 주요 범위로 한다.

Monitoring 파트는 Monitoring 구성 완료 후 백업 항목에 추가한다.

---

## 2. 백업 목표

```text
서비스 장애 또는 설정 손상 발생 시,
Restic 기반 백업 데이터를 이용하여 주요 서비스 구성 요소를 복구한다.
```

백업 대상은 다음과 같다.

| 대상 | 백업 내용 |
|---|---|
| Web Node | WordPress 파일, Docker 관련 설정, Web 서비스 구성 |
| DB Node | MariaDB dump, DB 설정 |
| Proxy Node | HAProxy 설정 파일 |
| Monitoring Node | Prometheus / Grafana / Alertmanager 설정, 추후 추가 |
| Backup Node | Restic repository, 백업 스크립트, 복구 절차 문서 |

---

## 3. 백업 방식

| 항목 | 내용 |
|---|---|
| 백업 도구 | Restic |
| 저장 위치 | Backup / Recovery Node 또는 Cinder Volume |
| 백업 방식 | 파일 백업 + DB dump + 설정 백업 |
| 실행 방식 | 스크립트 기반 실행 |
| 자동화 방향 | Ansible backup.yml 및 cron 연계 |
| 검증 방식 | snapshot 확인 및 restore test |

---

## 4. 현재 완료된 백업 범위

| 대상 | 상태 |
|---|---|
| Restic 설치 | 완료 |
| Web Node 백업 | 완료 |
| DB Node 백업 | 완료 |
| Proxy Node 백업 | 완료 |
| 복구 테스트 | 실시 |
| 백업 스크립트 | Monitoring 파트 제외 범위 작성 완료 |
| 복구 시나리오 5종 | 구성 완료 |
| 복구 시나리오 문서화 | 진행 중 |

---

## 5. 진행 중 / 예정 범위

| 대상 | 내용 | 상태 |
|---|---|---|
| Monitoring Node 백업 | Prometheus / Grafana / Alertmanager 설정 백업 | 예정 |
| Grafana Dashboard 백업 | Dashboard JSON 또는 설정 파일 백업 | 예정 |
| Alertmanager 설정 백업 | alertmanager.yml 백업 | 예정 |
| 복구 시나리오 문서화 | 5종 시나리오 상세 절차 작성 | 진행 |
| Ansible backup.yml | 구조 변경 반영 및 실행 검증 | 진행 |
| 자동 실행 | cron 또는 systemd timer 연계 | 검토 |

---

## 6. 백업 실행 절차

일반적인 백업 실행 절차는 다음과 같다.

```text
1. Backup / Recovery Node 접속
2. Restic repository 확인
3. Web Node 백업 실행
4. DB Node 백업 실행
5. Proxy Node 백업 실행
6. snapshot 목록 확인
7. 백업 결과 로그 저장
8. 필요 시 복구 테스트 실행
```

예시 명령:

```bash
restic snapshots
```

백업 스크립트 실행 예시:

```bash
bash scripts/backup/web-backup.sh
bash scripts/backup/backup.sh
```

실제 스크립트명은 저장소 내 최신 파일명을 기준으로 한다.

---

## 7. 복구 시나리오 5종

### 7.1 Web Service Recovery

| 항목 | 내용 |
|---|---|
| 장애 상황 | Web 파일 손상 또는 컨테이너 구성 오류 |
| 복구 대상 | Web 파일, Docker / Swarm 구성 |
| 검증 기준 | Web 서비스 정상 응답 |

### 7.2 DB Recovery

| 항목 | 내용 |
|---|---|
| 장애 상황 | DB 데이터 손상 또는 DB 접속 실패 |
| 복구 대상 | MariaDB dump 또는 백업 snapshot |
| 검증 기준 | DB 접속 및 WordPress 연동 정상 |

### 7.3 Proxy Recovery

| 항목 | 내용 |
|---|---|
| 장애 상황 | HAProxy 설정 손상 |
| 복구 대상 | `/etc/haproxy/haproxy.cfg` 등 Proxy 설정 |
| 검증 기준 | Proxy 경유 Web 응답 정상 |

### 7.4 Backup Repository Verification

| 항목 | 내용 |
|---|---|
| 장애 상황 | 백업 데이터 확인 필요 |
| 복구 대상 | Restic snapshot |
| 검증 기준 | snapshot 조회 및 restore 가능 |

### 7.5 Composite Recovery

| 항목 | 내용 |
|---|---|
| 장애 상황 | Web / DB / Proxy 중 복합 장애 |
| 복구 대상 | 서비스 구성 요소 전체 또는 일부 |
| 검증 기준 | 사용자 접속, DB 연동, Proxy 경유 응답 정상 |

---

## 8. 복구 검증 기준

복구 성공 기준은 다음과 같다.

| 검증 항목 | 성공 기준 |
|---|---|
| Restic snapshot | 조회 가능 |
| Restore 실행 | 오류 없이 완료 |
| Web 응답 | 정상 HTTP 응답 |
| DB 접속 | 계정 접속 가능 |
| Proxy 경유 | 사용자 요청 정상 전달 |
| 서비스 로그 | 치명적 오류 없음 |
| 문서화 | 복구 절차와 결과 기록 완료 |

---

## 9. 백업 / 복구 증빙

증빙 자료는 다음 항목을 포함한다.

```text
- Restic 설치 화면
- restic snapshots 결과
- 백업 스크립트 실행 결과
- 백업 저장소 용량 확인
- 복구 명령 실행 결과
- 복구 전 / 후 서비스 응답 비교
- DB 접속 검증 결과
- Proxy 설정 복구 결과
```

---

## 10. 멘토링 설명 기준

```text
백업은 단순 파일 복사가 아니라 Restic 기반 snapshot 구조로 구성했습니다.

현재 Web / DB / Proxy Node 백업과 복구 테스트를 실시했으며,
Monitoring 파트는 Grafana / Alertmanager 설정 완료 후 백업 항목에 추가할 예정입니다.

복구 시나리오는 5종으로 구성하여 단일 서비스 장애와 복합 장애 모두 설명할 수 있도록 문서화 중입니다.
```
