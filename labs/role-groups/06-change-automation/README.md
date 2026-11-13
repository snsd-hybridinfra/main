# Change Automation & Validation

변경 대상과 기준 상태를 확인하고 실패 시 원복을 검증합니다.

## 실행

저장소 루트에서 실행합니다.

```sh
python3 tools/run_role.py 06-change-automation
```

RESTCONF 실험의 RESTCONF·CLI 인터페이스 결과 3개를 비교하고, 승인 정책 실험의 읽기 전용 평가와 안전하지 않은 파라미터 거부를 확인합니다. `interfaces.json`과 `policy.txt`에 판정을 남깁니다.

[IDC 설정 백업과 변경·원복](idc/README.md) · [변경 작업 양식](idc/change-template.md)

## 실험

| 실험 | 검증 기록 |
|---|---|
| [RESTCONF / Python: API와 CLI 상태 대조](experiments/restconf-python/README.md) | 기존 로컬 검증 기록 |
| [Change Automation Approval & Policy Gates](experiments/automation-approval/README.md) | 이관 자료 · 개별 재검증 전 |
| [Continuous Verification & Evidence Freshness](experiments/continuous-verification/README.md) | 이관 자료 · 개별 재검증 전 |

<details>
<summary>다른 실험 보기</summary>

| 실험 | 검증 기록 |
|---|---|
| [Day-2 Operations & Failure Recovery Runbooks](experiments/day2-operations-runbooks/README.md) | 이관 자료 · 개별 재검증 전 |
| [Validation Harness and Synthetic Test Fixtures](experiments/validation-fixtures/README.md) | 이관 자료 · 개별 재검증 전 |
| [Bounded Remote Read-Only Validation & Evidence Pipeline](experiments/remote-readonly-validation/README.md) | 이관 자료 · 개별 재검증 전 |
| [Repository Quality Gates & Change Documentation](experiments/repository-quality-gates/README.md) | 이관 자료 · 개별 재검증 전 |

</details>

[전체 랩](../README.md) · [공통 실행 기록](../evidence/2026-11-12.json)
