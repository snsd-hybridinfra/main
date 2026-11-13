# Observability, SRE & Incident Triage

지표에서 이상을 발견하고 서비스 프로브·로그·알림으로 영향 범위를 확인합니다.

## 실행

저장소 루트에서 실행합니다.

```sh
python3 tools/run_role.py 05-observability-sre
```

이상 탐지 실험의 합성 메트릭을 검증·점수화하고 판정과 보고서를 생성합니다. 잘못된 데이터셋은 거부합니다. 결과는 `triage.json`, `triage.md`, `detection.csv`에 저장됩니다.

[IDC 관제 스택과 이벤트 상관분석](idc/README.md)

## 실험

| 실험 | 검증 기록 |
|---|---|
| [Deterministic Metric Anomaly Scoring and Reporting](experiments/metric-anomaly-scoring/README.md) | 이관 자료 · 개별 재검증 전 |
| [Service Observability, Probes & Traffic Health](experiments/service-observability/README.md) | 이관 자료 · 개별 재검증 전 |
| [Multi-Service Health Triage and Escalation](experiments/dandelion-health-triage/README.md) | 이관 자료 · 개별 재검증 전 |

<details>
<summary>다른 실험 보기</summary>

| 실험 | 검증 기록 |
|---|---|
| [Bounded Observability (Grafana / Loki / Alloy)](experiments/sanitized-observability/README.md) | 이관 자료 · 개별 재검증 전 |
| [OpenStack Monitoring VM + mTLS Deployment Reference](experiments/openstack-observability-deployment/README.md) | 이관 자료 · 개별 재검증 전 |

</details>

[전체 랩](../README.md) · [공통 실행 기록](../evidence/2026-11-12.json)
