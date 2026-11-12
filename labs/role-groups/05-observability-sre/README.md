# Observability, SRE & Incident Triage

**Primary role group** `05-observability-sre` · **이관 자료는 런타임 재검증 전**

이 역할군은 하나의 *운영 책임 경계*와 **재현 가능한 통합 검증 흐름**을 제공해. 원본 개별 랩은 유일한 소스의 진실이며 이 인덱스는 코드 복제/성공 상태 승격이 아님.

## 운영 목적
지표·로그·프로브를 관제 신호로 묶되 진단과 복구 승인을 분리

## 단일 실습 흐름
Sanitized Logs(18) + Service Metrics/Blackbox(26) + Monitoring Stack Provisioning(44) → Health Triage(42) → Threshold Anomaly Scoring(19)

## 소속 랩

| ID | 랩 (canonical) | 현재 출처 기반 상태 |
|---|---|---|
| 18 | [18-sanitized-observability](../../18-sanitized-observability/README.md) | 이관·재검증 대기 |
| 19 | [19-metric-anomaly-scoring](../../19-metric-anomaly-scoring/README.md) | 이관·재검증 대기 |
| 26 | [26-service-observability](../../26-service-observability/README.md) | 이관·재검증 대기 |
| 42 | [42-dandelion-health-triage](../../42-dandelion-health-triage/README.md) | 이관·재검증 대기 |
| 44 | [44-openstack-observability-deployment](../../44-openstack-observability-deployment/README.md) | 이관·재검증 대기 |

## 통합 대상, 중복 기능 정리
- 18+26+44: 수집·보존·접근정책을 하나의 관측 스택으로 설계
- 19+42: 임계값 점수와 서비스 헬스 판정을 구분하고 경보 품질 평가

## 역할군 공통 인터페이스

- **Input:** synthetic service logs, exporter metrics, HTTP/TCP probes, test outage
- **Output:** alert timeline, dashboard evidence, anomaly/health classification
- **Mandatory gate:** 미수집, 경보 누락, 오탐, 서비스 일부 장애, 로그 유출, 복구 확인

개별 랩에서 입력·출력 형식을 먼저 고정한 뒤 기능을 연결해. 기존 성공/실패 증적은 해당 랩에 유지하고, 통합 흐름의 결과는 **새로운 증적**을 따로 남겨야 해. 읽기 전용 관측과 변경·배포·삭제 코드는 같은 권한으로 실행하지 않음.

## 다음 조합 단계
1. 모든 랩의 의존성/하드코딩 경로를 해소하고 합성 데이터를 표준화한다.
2. 최소 단위 정상/거부/장애/복구 검증 후 통합 대상으로 승격한다.
3. 공통 인터페이스에 맞춰 각 랩을 조합하고 전체 흐름·회귀·롤백을 재검증한다.
4. 기존 `labs/NN-...` 경로는 링크/증적 보존을 위해 유지하며, 완성된 통합 코드만 향후 역할군 하위에 작성한다.

[전체 역할군 목록](../README.md) · [인터페이스 규격](../../../docs/lab-interface-contract.md)
