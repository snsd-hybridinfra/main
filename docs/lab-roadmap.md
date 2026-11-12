# 실습 로드맵

각 주제를 선택한 뉴스 원문, 내가 도출한 질문, 실제 증적과 한계는 [뉴스 → 기술 실습 기록](news-to-labs.md)에 있습니다.

상태 표기는 `계획`, `설계`, `로컬 검증`, `런타임 검증`을 사용합니다. 기존 01~14번 실습만 컨테이너·코드·합성 모델 또는 임시 로컬 클러스터에서 **로컬 검증** 상태입니다. 새 15~48번은 프로젝트 저장소에서 선별 이관·재구성했지만 **아직 실행 재검증 전**입니다. 실제 운영 환경에서 검증한 실습은 없습니다.

| 순서 | 주제 | 직접 확인할 질문 | 남길 증적 |
|---|---|---|---|
| 1 | [BGP/ECMP Spine-Leaf](../labs/01-bgp-ecmp/README.md) — 로컬 검증 | 링크 또는 Spine 장애 후 경로가 수렴하고 통신이 유지되는가? | [설정과 실행 출력](../labs/01-bgp-ecmp/evidence/2026-09-29.txt), 장애 전후 경로·ping |
| 2 | [EVPN/VXLAN](../labs/02-evpn-vxlan/README.md) — 로컬 검증 | 분리된 세그먼트의 허용·거부 통신이 의도대로 동작하는가? | [BGP EVPN·VNI·FDB 및 ping 출력](../labs/02-evpn-vxlan/evidence/2026-09-29.txt) |
| 3 | [RESTCONF/Python](../labs/03-restconf-python/README.md) — 로컬 검증 | API 조회 결과가 장비 CLI 상태와 일치하고 인증 실패 시 비교를 멈추는가? | [합성 인터페이스 3개 일치·불일치 0·HTTP 401 거부](../labs/03-restconf-python/evidence/2026-09-29.json); 실제 장비 대기 |
| 4 | [IAM/STS](../labs/04-iam-sts/README.md) — 로컬 검증 | 신뢰 관계·역할·세션 정책·명시적 거부로 Workload Identity 행동 범위를 줄일 수 있는가? | [합성 정책 판정 7/7 일치](../labs/04-iam-sts/evidence/2026-09-28.json); AWS/Azure 발급·만료·Resource Lock은 미검증 |
| 5 | [백업·복구](../labs/05-backup-recovery/README.md) — 로컬 검증 | 주 사이트 모델이 사라졌을 때 격리 백업으로 다른 엔드포인트를 얼마나 빨리 복구하는가? | [새 엔드포인트 RTO 1.633초·손실 2건·기존 엔드포인트 중단 유지](../labs/05-backup-recovery/evidence/2026-10-09.json); 실제 사이트·트래픽 전환은 미검증 |
| 6 | [AAA/RADIUS](../labs/06-aaa-radius/README.md) — 로컬 검증 | 등록된 사용자만 RADIUS 인증을 통과하는가? | [Access-Accept 1건·Access-Reject 2건](../labs/06-aaa-radius/evidence/2026-09-22.txt) |
| 7 | [AI Agent Security](../labs/07-ai-agent-security/README.md) — 로컬 검증 | Agent ID와 도구·파일·통신·예산·합성 승인 경계가 지켜지는가? | [서명 Passport·폐기·Scope와 파일·네트워크·승인·예산 게이트 15개 판정](../labs/07-ai-agent-security/evidence/2026-10-18.json); 실제 Agent·ServiceNow·MXC 런타임 대기 |
| 8 | [AI DC Network](../labs/08-ai-dc-network/README.md) — 로컬 검증 | 공유 병목에서 TCP 처리량과 지연이 어떻게 바뀌는가? | [20 Mbit/s 가상 링크 측정](../labs/08-ai-dc-network/evidence/2026-09-22.json); RoCE/ECN/PFC는 미검증 |
| 9 | [Edge Load Balancer HA](../labs/09-load-balancer-ha/README.md) — 로컬 검증 | 관리 서비스를 사용자 트래픽과 분리하면서 백엔드 장애에도 HTTP를 유지할 수 있는가? | [관리 SSH 허용·사용자/관리망의 OT 직접 접근 거부·정상/장애/복구 HTTP](../labs/09-load-balancer-ha/evidence/2026-10-15.json); 실제 OT 장비·방화벽·VPN·CVE·HA는 미검증 |
| 10 | [Network Digital Twin](../labs/10-network-digital-twin/README.md) — 로컬 검증 | 읽기 전용 모델로 경로·정책·외부 의존성과 AIDC 통합 Control Plane의 환경별 관측 상태를 판정할 수 있는가? | [Fabric·Sovereign 경로와 Public·Private·On-Prem API 관측 판정](../labs/10-network-digital-twin/evidence/2026-10-02.json); 실제 장비·Cloud API·상용 Control Plane은 미검증 |
| 11 | [Vulnerability Prioritization](../labs/11-vulnerability-prioritization/README.md) — 로컬 검증 | KEV·공식 실제 악용·패치 권고를 자산 맥락과 합치면 조치 순서가 어떻게 달라지는가? | [P0 7건·P1 1건·P2 2건·P3 2건, 12개 자산 출처 일치와 KVM 적용 범위 3건](../labs/11-vulnerability-prioritization/evidence/2026-10-18.json); 실제 자산·패치는 미검증 |
| 12 | [AI Multi-Region Data Path](../labs/12-ai-multiregion-data-path/README.md) — 로컬 검증 | Hub 원본과 Spoke Cache로 반복 원본 요청을 줄이고 손상 파일만 복구할 수 있는가? | [Cold Miss 8·Warm Hit 8·손상 1건 감지·복구 후 전체 Hit](../labs/12-ai-multiregion-data-path/evidence/2026-10-06.json); AWS·Qumulo·HyperPod 대기 |
| 13 | [Kubernetes RBAC](../labs/13-kubernetes-rbac/README.md) — 로컬 검증 | Operator용 ServiceAccount를 Namespace 최소 권한으로 제한하고 허용·거부를 런타임에서 확인할 수 있는가? | [kind에서 허용 2개·거부 4개 모두 기대 일치](../labs/13-kubernetes-rbac/evidence/2026-09-30.json); Dell CSM·실제 Operator·Audit Log·운영 k3s는 미검증 |
| 14 | [Terraform Security Validation](../labs/14-terraform-security-validation/README.md) — 로컬 검증 | 문법상 유효한 공개 SSH 규칙을 배포 전에 찾고 수정본을 같은 정책으로 재검증할 수 있는가? | [Before CKV_AWS_24 실패 1건·After 통과 1건](../labs/14-terraform-security-validation/evidence/2026-10-06.json); AWS Apply·CI 차단·Continuum은 미검증 |

## 실습 README 공통 양식

1. 문제와 브리핑 출처
2. 범위·상태와 구성 환경
3. 토폴로지 및 설정
4. 정상 상태의 기대값과 실제 출력
5. 장애 또는 거부 경로 테스트
6. 복구와 재검증
7. 결과·한계·개인 프로젝트와의 연결

증적이 없으면 `Result`에 성공 문장을 먼저 채우지 않습니다. 장비 이미지·버전에 따라 명령이 다르면 사용 환경을 명시합니다.

## 기존 실험 저장소에서 이관한 랩 (실행 재검증 대기)

| 번호 | 랩 | 소스/상태 | 다음 검증 |
|---|---|---|---|
| 15 | [AWS 2-Tier VPC with Ansible](../labs/15-aws-2tier-vpc/README.md) | `test`에서 이관 / `NOT_REVALIDATED` | Bastion 접근 제한, ALB, 2AZ 통신, 비용·정리 확인 |
| 16 | [OpenStack Ansible Operations](../labs/16-openstack-ansible-operations/README.md) | `dandelion-cloud-automation`에서 선별 이관 / `NOT_REVALIDATED` | 프로비저닝 멱등성, 접근 거부, 서비스 관측, 백업·복구 독립 검증 |
| 17 | [Cloud Network & Access Guardrails](../labs/17-cloud-network-access-baselines/README.md) | `snsd-multicloud-ops`에서 선별 이관 / `NOT_REVALIDATED` | Terraform 네트워크 정책·Kubernetes RBAC 허용/거부 테스트 |
| 18 | [Bounded Observability](../labs/18-sanitized-observability/README.md) | `snsd-multicloud-ops`에서 선별 이관 / `NOT_REVALIDATED` | 로컬 Compose·권한·로그 수집·지속성 검증 |
| 19 | [Metric Anomaly Scoring](../labs/19-metric-anomaly-scoring/README.md) | `snsd-multicloud-ops`에서 선별 이관 / `NOT_REVALIDATED` | Python 합성 입력 처리·이상 점수·오류 데이터 검증 |
| 20 | [PostgreSQL Restic Verification](../labs/20-postgres-restic-verification/README.md) | `snsd-multicloud-ops`에서 선별 이관 / `NOT_REVALIDATED` | 격리 DB 백업·snapshot·무결성·권한 거부 검증 |
| 21 | [Change Automation & Approval](../labs/21-automation-approval/README.md) | `snsd-multicloud-ops` / `NOT_REVALIDATED` | 승인·위험 분류 독립 재검증 |
| 22 | [Continuous Verification](../labs/22-continuous-verification/README.md) | `snsd-multicloud-ops` / `NOT_REVALIDATED` | 증적 신선도·회귀·반복성 독립 재검증 |
| 23 | [Cost & Cleanup Guardrails](../labs/23-cost-cleanup-guardrails/README.md) | `snsd-multicloud-ops` / `NOT_REVALIDATED` | 비용·정리 정책 독립 재검증 |
| 24 | [Multi-cloud Network IaC](../labs/24-multicloud-network-iac/README.md) | `snsd-multicloud-ops` / `NOT_REVALIDATED` | AWS·Azure Terraform 독립 재검증 |
| 25 | [Container Supply Chain](../labs/25-container-supply-chain/README.md) | `snsd-multicloud-ops` / `NOT_REVALIDATED` | 컨테이너 빌드 공급망 독립 재검증 |
| 26 | [Service Observability](../labs/26-service-observability/README.md) | `snsd-multicloud-ops` / `NOT_REVALIDATED` | Prometheus·Blackbox·Nginx 독립 재검증 |
| 27 | [Self-Service Request API](../labs/27-self-service-request-api/README.md) | `snsd-multicloud-ops` / `NOT_REVALIDATED` | 신청 API·카탈로그 독립 재검증 |
| 28 | [Approval & Grant Lifecycle](../labs/28-approval-grant-lifecycle/README.md) | `snsd-multicloud-ops` / `NOT_REVALIDATED` | 승인·권한·만료 독립 재검증 |
| 29 | [Terraform Runner & Blueprints](../labs/29-terraform-runner-blueprints/README.md) | `snsd-multicloud-ops` / `NOT_REVALIDATED` | OpenStack 상품·실행기 독립 재검증 |
| 30 | [Agent & Data Contracts](../labs/30-agent-data-contracts/README.md) | `snsd-multicloud-ops` / `NOT_REVALIDATED` | Agent·NAS·금융 SaaS 경계 독립 재검증 |
| 31 | [Kubernetes GitOps](../labs/31-kubernetes-gitops/README.md) | `snsd-multicloud-ops` / `NOT_REVALIDATED` | 63개 매니페스트 독립 재검증 |
| 32 | [Zero Trust Baselines](../labs/32-security-baselines/README.md) | `snsd-multicloud-ops` / `NOT_REVALIDATED` | SSH·서비스·데이터 정책 독립 재검증 |
| 33 | [EVE-NG Assurance](../labs/33-eve-network-assurance/README.md) | `snsd-multicloud-ops` / `NOT_REVALIDATED` | 라우팅·읽기 전용 검증 독립 재검증 |

| 34 | [PostgreSQL Schema & Migrations](../labs/34-postgres-schema-migrations/README.md) | `snsd-multicloud-ops` / `NOT_REVALIDATED` | DB 스키마·Alembic·권한 검증 독립 재검증 |
| 35 | [Portal UI Contracts](../labs/35-portal-ui-contracts/README.md) | `snsd-multicloud-ops` / `NOT_REVALIDATED` | 관리자·사용자 UI 기본 셸, 외부 팀 UI 제외 독립 재검증 |
| 36 | [Day-2 Operations Runbooks](../labs/36-day2-operations-runbooks/README.md) | `snsd-multicloud-ops` / `NOT_REVALIDATED` | 운영·배포·장애·복구 절차 독립 재검증 |
| 37 | [Validation Fixtures](../labs/37-validation-fixtures/README.md) | `snsd-multicloud-ops` / `NOT_REVALIDATED` | 테스트·합성 데이터·거부 케이스 독립 재검증 |
| 38 | [Identity & Device Assurance](../labs/38-identity-device-assurance/README.md) | `snsd-multicloud-ops` / `NOT_REVALIDATED` | 주체·역할·기기 신뢰 정책 독립 재검증 |
| 39 | [k3s Ansible Bootstrap](../labs/39-k3s-ansible-bootstrap/README.md) | `snsd-multicloud-ops` / `NOT_REVALIDATED` | 단일 노드 k3s Ansible 구성 독립 재검증 |
| 40 | [Zero Trust Package Contracts](../labs/40-zero-trust-package-contracts/README.md) | `snsd-multicloud-ops` / `NOT_REVALIDATED` | 보안 패키지·검증·롤백 계약 독립 재검증 |

| 41 | [Dandelion Restic Recovery](../labs/41-dandelion-restic-recovery/README.md) | `Team Dandelion` / `NOT_REVALIDATED` | 다중 서비스 Restic 복구 시나리오 독립 재검증 |
| 42 | [Dandelion Health Triage](../labs/42-dandelion-health-triage/README.md) | `Team Dandelion` / `NOT_REVALIDATED` | Web·DB·Proxy 상태 점검·자동복구 위험 분리 독립 재검증 |
| 43 | [Dandelion Service Topology](../labs/43-dandelion-service-topology/README.md) | `Team Dandelion` / `NOT_REVALIDATED` | OpenStack·HAProxy·WordPress·MariaDB 설계 독립 재검증 |
| 44 | [OpenStack Observability Deployment](../labs/44-openstack-observability-deployment/README.md) | `snsd-multicloud-ops` / `NOT_REVALIDATED` | Terraform·Ansible·mTLS 모니터링 배포 소스 독립 재검증 |
| 45 | [Remote Read-Only Validation](../labs/45-remote-readonly-validation/README.md) | `snsd-multicloud-ops` / `NOT_REVALIDATED` | EVE-NG·라우터·OpenStack 검증 및 증적 독립 재검증 |
| 46 | [Zero Trust Target Architecture](../labs/46-zero-trust-target-architecture/README.md) | `snsd-multicloud-ops` / `NOT_REVALIDATED` | 아키텍처·수용 기준·의존성 독립 재검증 |
| 47 | [Repository Quality Gates](../labs/47-repository-quality-gates/README.md) | `Team Dandelion` / `NOT_REVALIDATED` | CI 검증·리뷰·문서 자동화 독립 재검증 |
| 48 | [Restic Restore & Maintenance](../labs/48-restic-restore-maintenance/README.md) | `snsd-multicloud-ops` / `NOT_REVALIDATED` | 복원·유지보수·systemd 타이머 독립 재검증 |

**운영 원칙:** 랩을 독립적으로 검증한 후, 목적이 명확해질 때만 여러 랩을 조합해 프로젝트를 만듭니다. 새 프로젝트 완성 상태는 랩별 검증 상태와 별도로 판정합니다. 원본 이관 상세는 [이관 대장](migration-register.md)을 참조합니다.
