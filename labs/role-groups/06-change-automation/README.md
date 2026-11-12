# Change Automation & Validation

변경 대상과 기준 상태를 확인하고 실패 시 원복을 검증합니다.

## 실행

저장소 루트에서 실행합니다.

```sh
python3 tools/run_role.py 06-change-automation
```

Lab 03의 RESTCONF·CLI 인터페이스 결과 3개를 비교하고, Lab 21의 읽기 전용 평가와 안전하지 않은 파라미터 거부를 확인합니다. `interfaces.json`과 `policy.txt`에 판정을 남깁니다.

[IDC 설정 백업과 변경·원복](idc/README.md) · [변경 작업 양식](idc/change-template.md)

## 번호 랩

| ID | 실습과 자료 | 번호 랩의 기록 |
|---|---|---|
| 03 | [03-restconf-python](../../03-restconf-python/README.md) | 기존 로컬 증적 |
| 21 | [21-automation-approval](../../21-automation-approval/README.md) | 이관 참고 |
| 22 | [22-continuous-verification](../../22-continuous-verification/README.md) | 이관 참고 |
| 36 | [36-day2-operations-runbooks](../../36-day2-operations-runbooks/README.md) | 이관 참고 |
| 37 | [37-validation-fixtures](../../37-validation-fixtures/README.md) | 이관 참고 |
| 45 | [45-remote-readonly-validation](../../45-remote-readonly-validation/README.md) | 이관 참고 |
| 47 | [47-repository-quality-gates](../../47-repository-quality-gates/README.md) | 이관 참고 |

[역할 랩 인덱스](../README.md) · [대표 사례 검증 결과](../evidence/2026-11-12.json)
