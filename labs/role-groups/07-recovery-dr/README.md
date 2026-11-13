# Backup, Recovery & Operational Resilience

장애가 서비스에 미친 영향을 측정하고 복구 후 상태를 검증합니다.

## 실행

저장소 루트에서 실행합니다.

```sh
python3 tools/run_role.py 07-recovery-dr
```

백업·복구 실험은 임시 로컬 HTTP 서비스와 SQLite 스냅샷으로 장애와 복구를 재현합니다. 복구 후 서비스 상태, 스냅샷 누락 거부, 데이터 손실과 소요 시간을 `site-restore.json`에서 확인합니다.

[IDC 장애 5종 재현](idc/README.md) · [실측 보고서](idc/validation.md) · [장애 처리 양식](idc/incident-template.md)

## 실험

| 실험 | 검증 기록 |
|---|---|
| [백업·복구: 합성 서비스의 RTO/RPO 측정](experiments/backup-recovery/README.md) | 기존 로컬 검증 기록 |
| [PostgreSQL Backup + Restic Evidence Verification](experiments/postgres-restic-verification/README.md) | 이관 자료 · 개별 재검증 전 |
| [Restic Restore, Maintenance & Scheduled Backups](experiments/restic-restore-maintenance/README.md) | 이관 자료 · 개별 재검증 전 |

<details>
<summary>다른 실험 보기</summary>

| 실험 | 검증 기록 |
|---|---|
| [Dandelion Restic Backup and Recovery Scenarios](experiments/dandelion-restic-recovery/README.md) | 이관 자료 · 개별 재검증 전 |

</details>

[전체 랩](../README.md) · [공통 실행 기록](../evidence/2026-11-12.json)
