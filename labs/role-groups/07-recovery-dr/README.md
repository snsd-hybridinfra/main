# Backup, Recovery & Operational Resilience

**Primary role group** `07-recovery-dr` · **이관 자료는 런타임 재검증 전**

이 역할군은 하나의 *운영 책임 경계*와 **재현 가능한 통합 검증 흐름**을 제공해. 원본 개별 랩은 유일한 소스의 진실이며 이 인덱스는 코드 복제/성공 상태 승격이 아님.

## 운영 목적
백업 생성·무결성·권한·복원·RTO/RPO를 독립 계측

## 단일 실습 흐름
Synthetic Recovery(05) → PostgreSQL/Restic Integrity(20) → Multi-Service Scenarios(41) → Scheduled Restore and Retention(48)

## 소속 랩

| ID | 랩 (canonical) | 현재 출처 기반 상태 |
|---|---|---|
| 05 | [05-backup-recovery](../../05-backup-recovery/README.md) | 기존 로컬 검증 기록 |
| 20 | [20-postgres-restic-verification](../../20-postgres-restic-verification/README.md) | 이관·재검증 대기 |
| 41 | [41-dandelion-restic-recovery](../../41-dandelion-restic-recovery/README.md) | 이관·재검증 대기 |
| 48 | [48-restic-restore-maintenance](../../48-restic-restore-maintenance/README.md) | 이관·재검증 대기 |

## 통합 대상, 중복 기능 정리
- 20+48: 동일 Restic repo를 읽기 전용 증적 검증 / 별도 유지보수 승인으로 분할
- 05+41: 서비스 복원 시점·손실량·장애 전후 의존성 정의를 공통화

## 역할군 공통 인터페이스

- **Input:** synthetic DB/content, disposable Restic repo, signed snapshot, test outage
- **Output:** checksum report, restore log, actual RTO/RPO, access-denial evidence
- **Mandatory gate:** 잘못된 백업, 권한 제한, 데이터 손실, 검증 없는 prune, 다른 DB 덮어쓰기, 복원 실패

개별 랩에서 입력·출력 형식을 먼저 고정한 뒤 기능을 연결해. 기존 성공/실패 증적은 해당 랩에 유지하고, 통합 흐름의 결과는 **새로운 증적**을 따로 남겨야 해. 읽기 전용 관측과 변경·배포·삭제 코드는 같은 권한으로 실행하지 않음.

## 다음 조합 단계
1. 모든 랩의 의존성/하드코딩 경로를 해소하고 합성 데이터를 표준화한다.
2. 최소 단위 정상/거부/장애/복구 검증 후 통합 대상으로 승격한다.
3. 공통 인터페이스에 맞춰 각 랩을 조합하고 전체 흐름·회귀·롤백을 재검증한다.
4. 기존 `labs/NN-...` 경로는 링크/증적 보존을 위해 유지하며, 완성된 통합 코드만 향후 역할군 하위에 작성한다.

[전체 역할군 목록](../README.md) · [인터페이스 규격](../../../docs/lab-interface-contract.md)
