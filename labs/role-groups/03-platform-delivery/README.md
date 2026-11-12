# Platform Engineering & Application Delivery

**Primary role group** `03-platform-delivery` · **이관 자료는 런타임 재검증 전**

이 역할군은 하나의 *운영 책임 경계*와 **재현 가능한 통합 검증 흐름**을 제공해. 원본 개별 랩은 유일한 소스의 진실이며 이 인덱스는 코드 복제/성공 상태 승격이 아님.

## 운영 목적
요청 → 승인 → 인프라 작업 → 배포 → 권한 폐기의 IDP 수명주기를 분리 검증

## 단일 실습 흐름
DB Migration(34) → Request API(27) → Approval/Grant(28) → Terraform Runner(29) → Kubernetes Delivery(31) → Portal/Edge(35,49) → Agent/Data Contracts(30) → Supply Chain(25)

## 소속 랩

| ID | 랩 (canonical) | 현재 출처 기반 상태 |
|---|---|---|
| 25 | [25-container-supply-chain](../../25-container-supply-chain/README.md) | 이관·재검증 대기 |
| 27 | [27-self-service-request-api](../../27-self-service-request-api/README.md) | 이관·재검증 대기 |
| 28 | [28-approval-grant-lifecycle](../../28-approval-grant-lifecycle/README.md) | 이관·재검증 대기 |
| 29 | [29-terraform-runner-blueprints](../../29-terraform-runner-blueprints/README.md) | 이관·재검증 대기 |
| 30 | [30-agent-data-contracts](../../30-agent-data-contracts/README.md) | 이관·재검증 대기 |
| 31 | [31-kubernetes-gitops](../../31-kubernetes-gitops/README.md) | 이관·재검증 대기 |
| 34 | [34-postgres-schema-migrations](../../34-postgres-schema-migrations/README.md) | 이관·재검증 대기 |
| 35 | [35-portal-ui-contracts](../../35-portal-ui-contracts/README.md) | 이관·재검증 대기 |
| 49 | [49-edge-security-service-contracts](../../49-edge-security-service-contracts/README.md) | 이관·재검증 대기 |

## 통합 대상, 중복 기능 정리
- 27+28+29+34: API 계약과 트랜잭션 상태를 공통 synthetic request_id로 연결
- 25+31+49: 빌드 증적·서명/정책·Ingress/WAF 차단과 릴리스 게이트 연결

## 역할군 공통 인터페이스

- **Input:** synthetic identity, request payload, approval token, blueprint, pinned image
- **Output:** request state timeline, provisioning plan, authorization log, deployment denial evidence
- **Mandatory gate:** 승인 없는 실행, 이중 신청, 만료 권한, 취약 이미지, tenant 우회, 롤백 실패

개별 랩에서 입력·출력 형식을 먼저 고정한 뒤 기능을 연결해. 기존 성공/실패 증적은 해당 랩에 유지하고, 통합 흐름의 결과는 **새로운 증적**을 따로 남겨야 해. 읽기 전용 관측과 변경·배포·삭제 코드는 같은 권한으로 실행하지 않음.

## 다음 조합 단계
1. 모든 랩의 의존성/하드코딩 경로를 해소하고 합성 데이터를 표준화한다.
2. 최소 단위 정상/거부/장애/복구 검증 후 통합 대상으로 승격한다.
3. 공통 인터페이스에 맞춰 각 랩을 조합하고 전체 흐름·회귀·롤백을 재검증한다.
4. 기존 `labs/NN-...` 경로는 링크/증적 보존을 위해 유지하며, 완성된 통합 코드만 향후 역할군 하위에 작성한다.

[전체 역할군 목록](../README.md) · [인터페이스 규격](../../../docs/lab-interface-contract.md)
