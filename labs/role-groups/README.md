# Labs by operational role

**51개 개별 랩 → 7개 주 역할군** (각 랩은 정확히 하나의 주 역할군 소속)

개별 실습 코드를 복제·삭제하거나 실행 성공 상태를 승격하지 않고, **역할별 책임·표준 입력/출력·실습 흐름·공동 검증 게이트**를 하나로 묶었어. 소스 코드와 과거 증적은 기존 `labs/NN-...`에 둬서 링크와 Git 이력 분리를 방지해.

| Role group | Lab count | Goal |
|---|---:|---|
| [Network Fabric & Traffic Engineering](01-network-fabric/README.md) | 8 | L2/L3 underlay·overlay·경로·로드밸런싱과 장애 우회 경로의 재현성 |
| [Cloud Foundations, IaC & Provisioning](02-cloud-foundation/README.md) | 9 | AWS·Azure·OpenStack의 네트워크/VM 자원을 안전하게 선언·검증·폐기 |
| [Platform Engineering & Application Delivery](03-platform-delivery/README.md) | 9 | 요청 → 승인 → 인프라 작업 → 배포 → 권한 폐기의 IDP 수명주기를 분리 검증 |
| [Security, Identity & Zero Trust](04-security-trust/README.md) | 9 | 자산·사용자·워크로드 식별부터 정책 집행과 증적 유효성까지 검증 |
| [Observability, SRE & Incident Triage](05-observability-sre/README.md) | 5 | 지표·로그·프로브를 관제 신호로 묶되 진단과 복구 승인을 분리 |
| [Operations, Change Validation & Evidence](06-change-automation/README.md) | 7 | 장비·클라우드 변경 전 읽기 → 위험 승인 → 실행 제안 → 결과·회귀 증적 |
| [Backup, Recovery & Operational Resilience](07-recovery-dr/README.md) | 4 | 백업 생성·무결성·권한·복원·RTO/RPO를 독립 계측 |

**검증 상태:** 기존 Lab 01–14는 이전 로컬 검증 기록 유지, Lab 15–51은 source-extracted/NOT_REVALIDATED. 어떤 그룹도 현재 통합 테스트 PASS 상태가 아니야.

[역할별 기계 판독형 카탈로그](manifest.json) · [중복/통합 가이드](../../docs/role-consolidation-plan.md)
