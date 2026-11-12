# Observability, SRE & Incident Triage

지표에서 이상을 발견하고 서비스 프로브·로그·알림으로 영향 범위를 확인합니다.

## 실행

저장소 루트에서 실행합니다.

```sh
python3 tools/run_role.py 05-observability-sre
```

Lab 19의 합성 메트릭을 검증·점수화하고 판정과 보고서를 생성합니다. 잘못된 데이터셋은 거부합니다. 결과는 `triage.json`, `triage.md`, `detection.csv`에 저장됩니다.

[IDC 관제 스택과 이벤트 상관분석](idc/README.md)

## 번호 랩

| ID | 실습과 자료 | 번호 랩의 기록 |
|---|---|---|
| 18 | [18-sanitized-observability](../../18-sanitized-observability/README.md) | 이관 참고 |
| 19 | [19-metric-anomaly-scoring](../../19-metric-anomaly-scoring/README.md) | 이관 참고 |
| 26 | [26-service-observability](../../26-service-observability/README.md) | 이관 참고 |
| 42 | [42-dandelion-health-triage](../../42-dandelion-health-triage/README.md) | 이관 참고 |
| 44 | [44-openstack-observability-deployment](../../44-openstack-observability-deployment/README.md) | 이관 참고 |

[역할 랩 인덱스](../README.md) · [대표 사례 검증 결과](../evidence/2026-11-12.json)
