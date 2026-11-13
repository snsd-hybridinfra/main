# Platform Engineering & Application Delivery

개발자 요청이 어떤 실행 프로파일과 의존성으로 이어지는지 확인합니다.

## 실행

저장소 루트에서 실행합니다.

```sh
python3 tools/run_role.py 03-platform-delivery
```

요청 해석기와 Terraform 실행 카탈로그를 연결합니다. 개발 VM 요청은 로컬 모듈로 해석되고, 개발 API 요청은 필수 어댑터 및 의존성이 준비될 때까지 차단됩니다. 두 요청의 digest와 배포 권한 상태를 `blueprints.json`에서 확인합니다.

실습 범위는 카탈로그와 배포 조건 검증입니다.

## 실험

| 실험 | 검증 기록 |
|---|---|
| [운영 실험 카탈로그 UI](experiments/portfolio-catalog/README.md) | 로컬 로직·링크 검증 |
| [Self-Service Infrastructure Request API](experiments/self-service-request-api/README.md) | 이관 자료 · 개별 재검증 전 |
| [Kubernetes Manifest, Policy & GitOps Source](experiments/kubernetes-gitops/README.md) | 이관 자료 · 개별 재검증 전 |
| [Container Build Supply Chain & Restricted Runner](experiments/container-supply-chain/README.md) | 이관 자료 · 개별 재검증 전 |

<details>
<summary>다른 실험 보기</summary>

| 실험 | 검증 기록 |
|---|---|
| [Approval, Access Grant and Expiration](experiments/approval-grant-lifecycle/README.md) | 이관 자료 · 개별 재검증 전 |
| [OpenStack Terraform Blueprints & Job Runner](experiments/terraform-runner-blueprints/README.md) | 이관 자료 · 개별 재검증 전 |
| [Agent Sandbox & Data Exchange Contracts](experiments/agent-data-contracts/README.md) | 이관 자료 · 개별 재검증 전 |
| [PostgreSQL Schema, RBAC and Alembic Migrations](experiments/postgres-schema-migrations/README.md) | 이관 자료 · 개별 재검증 전 |
| [Self-Service / Admin Portal UI Contracts](experiments/portal-ui-contracts/README.md) | 이관 자료 · 개별 재검증 전 |
| [Edge WAF, AuthN/AuthZ and Service API Contracts](experiments/edge-security-service-contracts/README.md) | 이관 자료 · 개별 재검증 전 |

</details>

[전체 랩](../README.md) · [공통 실행 기록](../evidence/2026-11-12.json)
