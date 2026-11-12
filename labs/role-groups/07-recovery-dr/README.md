# Backup, Recovery & Operational Resilience

장애가 서비스에 미친 영향을 측정하고 복구 후 상태를 검증합니다.

## 실행

저장소 루트에서 실행합니다.

```sh
python3 tools/run_role.py 07-recovery-dr
```

Lab 05가 임시 로컬 HTTP 서비스와 SQLite 스냅샷으로 장애와 복구를 재현합니다. 복구 후 서비스 상태, 스냅샷 누락 거부, 데이터 손실과 소요 시간을 `site-restore.json`에서 확인합니다.

[IDC 장애 5종 재현](idc/README.md) · [실측 보고서](idc/validation.md) · [장애 처리 양식](idc/incident-template.md)

## 번호 랩

| ID | 실습과 자료 | 번호 랩의 기록 |
|---|---|---|
| 05 | [05-backup-recovery](../../05-backup-recovery/README.md) | 기존 로컬 증적 |
| 20 | [20-postgres-restic-verification](../../20-postgres-restic-verification/README.md) | 이관 참고 |
| 41 | [41-dandelion-restic-recovery](../../41-dandelion-restic-recovery/README.md) | 이관 참고 |
| 48 | [48-restic-restore-maintenance](../../48-restic-restore-maintenance/README.md) | 이관 참고 |

[역할 랩 인덱스](../README.md) · [대표 사례 검증 결과](../evidence/2026-11-12.json)
