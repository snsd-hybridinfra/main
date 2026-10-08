# 독립 실습과 구현 프로젝트의 연결

## 저장소 역할

| 저장소 | 역할 | 상태 권위 |
|---|---|---|
| `F:\main` | 뉴스 원문에서 기술 질문을 도출하고 독립 실습과 증적을 축적 | 이 저장소의 `README`, `docs/news-to-labs.md`, 각 실습 README |
| [snsd-multicloud-ops](https://github.com/snsd-hybirdinfra/snsd-multicloud-ops) | 가상 증권사 Hybrid-Ready Private Cloud IDP 구현 | 서브 프로젝트의 플랫폼 기준선·구현 로드맵·Zero Trust 권위 문서 |

독립 실습의 통과가 서브 프로젝트 통합 완료를 뜻하지 않습니다. 서브 프로젝트의 파일이 존재한다는 사실도 배포·런타임 검증을 뜻하지 않습니다.

## 서브 프로젝트 현재 상태

2026-09-28에 서브 프로젝트의 `README`, `docs/platform/implementation-roadmap.md`, `docs/platform/architecture-baseline.yaml`을 대조했습니다.

| 영역 | 현재 상태 |
|---|---|
| Authority & Inventory | `COMPLETED_LOCAL` |
| Private IaaS Golden Path | `IN_PROGRESS_LOCAL` |
| k3s PaaS Golden Path | `PARTIAL` |
| Financial Network Fabric | `DESIGN_ONLY` |
| Integrated Operations | `PARTIAL` |
| Public Cloud Adapter | `DEFERRED` |
| 플랫폼 종단 간 런타임 | `NOT_VALIDATED` |

따라서 프로젝트 표현은 **Hybrid-Ready Private Cloud IDP**를 유지합니다.

## 실습 연결 지도

| main 실습 | 서브 프로젝트에서 연결되는 문제 | 적용 상태 |
|---|---|---|
| 01 BGP/ECMP, 02 EVPN/VXLAN | 금융 네트워크 언더레이의 경로 이중화와 세그멘테이션 | 독립 실습 완료, 서브 프로젝트 Network Fabric은 `DESIGN_ONLY` |
| 03 RESTCONF/Python | 장비 상태 수집과 운영 자동화 | 합성 RESTCONF·SSH CLI 로컬 검증; 실제 장비 대조 대기 |
| 04 IAM/STS | 향후 퍼블릭 클라우드 어댑터와 Agent Workload Identity | 합성 정책 판정 로컬 검증; 실제 STS/Azure와 어댑터는 `DEFERRED` |
| 05 Backup & Recovery | 플랫폼 수명주기와 복구 증적 | 합성 서비스 로컬 검증; 통합 복구는 `PARTIAL` |
| 06 AAA/RADIUS | 관리망 접근 제어 | 독립 로컬 검증; 금융망 적용 미검증 |
| 07 AI Agent Security | AI Agent Sandbox의 Identity·파일·통신·예산·승인 경계 | 독립 게이트 검증; 서브 프로젝트는 `PARTIALLY_IMPLEMENTED_LOCAL / NOT_VALIDATED` |
| 08 AI DC Network | 향후 GPU 워크로드의 병목과 관측 | 제한된 가상 링크 검증; GPU/RDMA 미검증 |
| 09 Edge Load Balancer HA | 포털·서비스 경계의 관리 접근 분리와 가용성 | Nginx·OpenSSH 합성 검증; Cisco SD-WAN Manager 등 실제 경계 장비와 플랫폼 통합은 미검증 |
| 10 Network Digital Twin | 변경 전 경로·정책, 외부 의존성, AIDC Control Plane의 환경별 관측 상태 검증 | Fabric·Sovereign·AIDC 합성 모델 검증; 실제 장비·Cloud API·플랫폼 통합 미검증 |
| 11 Vulnerability Prioritization | 네트워크·플랫폼 자산의 패치 우선순위 | CISA KEV·공식 실제 악용·패치 권고와 합성 자산 맥락 검증; 실제 CMDB·버전·노출·패치 미검증 |
| 12 AI Multi-Region Data Path | 향후 GPU Compute와 Dataset 배치 판단 | 로컬 파일 Cache의 Hit·무결성·단일 파일 복구 검증; Public Cloud Adapter가 `DEFERRED`라 실제 AWS·Qumulo·HyperPod 미검증 |
| 13 Kubernetes RBAC | k3s PaaS의 자동화 ServiceAccount 최소 권한 | 임시 kind 런타임 검증; Dell CSM·서브 프로젝트 k3s 적용·Audit Log는 미검증 |
| 14 Terraform Security Validation | Terraform 변경의 배포 전 정책 검사 | 공개 SSH 탐지·수정·재검증 로컬 실행; 서브 프로젝트 CI 적용과 AWS 배포는 미검증 |

## 승격 조건

독립 실습을 서브 프로젝트 성과로 연결하려면 다음이 모두 필요합니다.

1. 서브 프로젝트의 권위 문서에 적용 범위와 소유자를 기록합니다.
2. 실제 대상의 구성·버전·경계를 확인합니다.
3. 정상·거부·장애·복구 검증을 수행합니다.
4. 정제 증적을 해당 프로젝트의 승인된 증적 위치에 저장합니다.
5. 상태 결정 문서가 구현과 증적을 근거로 승격합니다.
