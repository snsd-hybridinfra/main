# News-to-Lab Infrastructure Portfolio

「IT·보안 데일리 브리핑」에서 운영 문제를 찾고, 원문을 확인한 뒤 직접 시험 가능한 기술 질문으로 바꾸는 네트워크·클라우드·보안·AI 인프라 포트폴리오입니다.

```text
브리핑 → 원문 확인 → 기술 질문 → 실습 설계 → 정상·장애·거부 검증 → 증적 → 한계 → 프로젝트 적용
```

기사에 나온 사실과 내가 만든 구현을 분리합니다. 실행하지 않은 구성은 성공으로 적지 않으며, 합성 환경과 실제 런타임을 같은 상태로 표시하지 않습니다.

## 누적 브리핑 — 2026년 11월 2일 (월) 정리

[브리핑 모음](docs/briefings/README.md)에 2026-09-08~11-02를 대상으로 한 분야별 종합, 10월 말 후속 이슈, 컨퍼런스 기술자료와 다음 실습을 정리했습니다. 전체 날짜의 기사 원문을 모두 확보한 것은 아니며 [확보 범위](docs/briefings/source-register.md)에 누락 구간을 표시했습니다.

- [누적 핵심 정리](docs/briefings/cumulative-summary.md): 네트워크·클라우드·보안·자동화·AI 인프라·커리어와 기존 14개 랩 연결
- [10월 말 후속 정리](docs/briefings/latest-updates.md): 공식 자료로 확인한 SD-WAN·PAN-OS·SSL VPN 이슈
- [컨퍼런스 노트](docs/briefings/conference-notes.md): Cisco Live·OpenStack 기술과 데이터센터코리아 사전 선별
- [다음 학습·실습](docs/briefings/next-actions.md): 경로 설명 → 변경 검증 → 관리 경계 보안의 우선순위

이번 업데이트는 문서 정리입니다. 기존 랩을 새로 실행하거나 검증 상태를 변경하지 않았습니다.

## 현재 상태

| 구분 | 수량 | 의미 |
|---|---:|---|
| 등록 랩 | 48 | 기존 로컬 검증 기록 14개 + 선별 이관·재구성 랩 34개 |
| 기존 로컬 검증 | 14 | 코드·컨테이너·합성 모델 및 임시 로컬 클러스터에서 증적 확보 |
| 이관·재검증 대기 | 34 | 소스 추출·정적 보존 단계, 독립 실행·통합 검증 전 |
| 실제 운영 검증 | 0 | 운영·고객 환경 성과를 주장하지 않음 |

## 실습 카탈로그

### Network & Data Center

| 실습 | 상태 | 확인한 결과 |
|---|---|---|
| [01 BGP/ECMP](labs/01-bgp-ecmp/README.md) | 로컬 검증 | 정상 경로 2개, Spine 장애 후 대체 경로 1개와 ping 3/3 |
| [02 EVPN/VXLAN](labs/02-evpn-vxlan/README.md) | 로컬 검증 | VNI 100·200 내부 통신과 VNI 간 격리 |
| [08 AI DC Network](labs/08-ai-dc-network/README.md) | 로컬 검증 | 20 Mbit/s 가상 병목의 처리량과 부하 중 지연 |
| [09 Edge Load Balancer HA](labs/09-load-balancer-ha/README.md) | 로컬 검증 | 관리망 SSH 허용, 사용자망의 OT 직접 접근 거부, 백엔드 장애 중 HTTP 유지 |
| [10 Network Digital Twin](labs/10-network-digital-twin/README.md) | 로컬 검증 | Fabric·Sovereign 경로와 AIDC 통합 Control Plane의 환경별 관측 사각지대 계산 |

### Cloud & Automation

| 실습 | 상태 | 확인한 결과 |
|---|---|---|
| [03 RESTCONF/Python](labs/03-restconf-python/README.md) | 로컬 검증 | 합성 장비 RESTCONF·SSH CLI 인터페이스 3개 일치, 인증 실패 거부 |
| [04 IAM/STS](labs/04-iam-sts/README.md) | 로컬 검증 | 신뢰 관계·세션 축소·명시적 거부 7개 정책 판정; AWS/Azure 런타임 대기 |
| [05 Backup & Recovery](labs/05-backup-recovery/README.md) | 로컬 검증 | 로컬 사이트 모델 장애 뒤 새 엔드포인트 복구 1.633초, 손실 2건 |
| [12 AI Multi-Region Data Path](labs/12-ai-multiregion-data-path/README.md) | 로컬 검증 | Cold Miss 8건, Warm Hit 8건, Cache 훼손 감지·단일 파일 복구·재검증 |

### Security & Operations

| 실습 | 상태 | 확인한 결과 |
|---|---|---|
| [06 AAA/RADIUS](labs/06-aaa-radius/README.md) | 로컬 검증 | 승인 1건, 거부 2건 |
| [07 AI Agent Security](labs/07-ai-agent-security/README.md) | 로컬 검증 | 서명된 Agent Passport·폐기·도구 Scope와 파일·통신·승인 경계의 허용·거부 |
| [11 Vulnerability Prioritization](labs/11-vulnerability-prioritization/README.md) | 로컬 검증 | KEV·실제 악용·관리 Plane 우선순위와 자체 KVM·AWS 관리형 적용 범위 판정 |
| [13 Kubernetes RBAC](labs/13-kubernetes-rbac/README.md) | 로컬 검증 | ServiceAccount 읽기 허용 2개와 Secret·삭제·Namespace 밖·ClusterRole 거부 4개 |
| [14 Terraform Security Validation](labs/14-terraform-security-validation/README.md) | 로컬 검증 | 공개 SSH 1건 탐지, CIDR 수정 후 같은 Checkov 규칙 통과 |

### Extracted Labs: Source-Migrated (NOT_REVALIDATED)

| 랩 | 원본 저장소 | 이관 상태 |
|---|---|---|
| [15 AWS 2-Tier VPC with Ansible](labs/15-aws-2tier-vpc/README.md) | private `test` | 보안 조정·중복 제거, 실행 재검증 대기 |
| [16 OpenStack Ansible Operations](labs/16-openstack-ansible-operations/README.md) | `dandelion-cloud-automation` | 팀 코드 일부 선별, 실행 재검증 대기 |
| [17 Cloud Network & Access Guardrails](labs/17-cloud-network-access-baselines/README.md) | `snsd-multicloud-ops` | 네트워크·RBAC 일부 선별, 실행 재검증 대기 |
| [18 Bounded Observability](labs/18-sanitized-observability/README.md) | `snsd-multicloud-ops` | Grafana·Loki·Alloy 로그 수집, 실행 재검증 대기 |
| [19 Metric Anomaly Scoring](labs/19-metric-anomaly-scoring/README.md) | `snsd-multicloud-ops` | 합성 메트릭 정적 점수화, 실행 재검증 대기 |
| [20 PostgreSQL Restic Verification](labs/20-postgres-restic-verification/README.md) | `snsd-multicloud-ops` | 제한된 백업·무결성 검증 코드, 실행 재검증 대기 |

자세한 원본 커밋·제외 범위·삭제 전 보존 조건은 [이관 대장](docs/migration-register.md)을 참고합니다. **이관은 검증이나 원본 전체 보존을 의미하지 않습니다.**

### Additional extracted labs (21–33)

| 랩 | 관심사 | 상태 |
|---|---|---|
| [21 Change Automation & Approval](labs/21-automation-approval/README.md) | 승인·위험 분류 | `NOT_REVALIDATED` |
| [22 Continuous Verification](labs/22-continuous-verification/README.md) | 증적 신선도·회귀·반복성 | `NOT_REVALIDATED` |
| [23 Cost & Cleanup Guardrails](labs/23-cost-cleanup-guardrails/README.md) | 비용·정리 정책 | `NOT_REVALIDATED` |
| [24 Multi-cloud Network IaC](labs/24-multicloud-network-iac/README.md) | AWS·Azure Terraform | `NOT_REVALIDATED` |
| [25 Container Supply Chain](labs/25-container-supply-chain/README.md) | 컨테이너 빌드 공급망 | `NOT_REVALIDATED` |
| [26 Service Observability](labs/26-service-observability/README.md) | Prometheus·Blackbox·Nginx | `NOT_REVALIDATED` |
| [27 Self-Service Request API](labs/27-self-service-request-api/README.md) | 신청 API·카탈로그 | `NOT_REVALIDATED` |
| [28 Approval & Grant Lifecycle](labs/28-approval-grant-lifecycle/README.md) | 승인·권한·만료 | `NOT_REVALIDATED` |
| [29 Terraform Runner & Blueprints](labs/29-terraform-runner-blueprints/README.md) | OpenStack 상품·실행기 | `NOT_REVALIDATED` |
| [30 Agent & Data Contracts](labs/30-agent-data-contracts/README.md) | Agent·NAS·금융 SaaS 경계 | `NOT_REVALIDATED` |
| [31 Kubernetes GitOps](labs/31-kubernetes-gitops/README.md) | 63개 매니페스트 | `NOT_REVALIDATED` |
| [32 Zero Trust Baselines](labs/32-security-baselines/README.md) | SSH·서비스·데이터 정책 | `NOT_REVALIDATED` |
| [33 EVE-NG Assurance](labs/33-eve-network-assurance/README.md) | 라우팅·읽기 전용 검증 | `NOT_REVALIDATED` |

[원본 파일 1,252개 목록·SHA](docs/migration/snsd-multicloud-ops-source-file-manifest.tsv)는 **백업이 아닌 인덱스**입니다. 원본에서 미이관 자료가 남아 있으므로 삭제하지 않았습니다.

### Additional extracted labs (34–40)

| 랩 | 재사용 범위 | 소스 파일 | 상태 |
|---|---|---:|---|
| [34 PostgreSQL Schema & Migrations](labs/34-postgres-schema-migrations/README.md) | DB 스키마·Alembic·권한 검증 | 26 | `NOT_REVALIDATED` |
| [35 Portal UI Contracts](labs/35-portal-ui-contracts/README.md) | 관리자·사용자 UI 기본 셸, 외부 팀 UI 제외 | 10 | `NOT_REVALIDATED` |
| [36 Day-2 Operations Runbooks](labs/36-day2-operations-runbooks/README.md) | 운영·배포·장애·복구 절차 | 40 | `NOT_REVALIDATED` |
| [37 Validation Fixtures](labs/37-validation-fixtures/README.md) | 테스트·합성 데이터·거부 케이스 | 36 | `NOT_REVALIDATED` |
| [38 Identity & Device Assurance](labs/38-identity-device-assurance/README.md) | 주체·역할·기기 신뢰 정책 | 12 | `NOT_REVALIDATED` |
| [39 k3s Ansible Bootstrap](labs/39-k3s-ansible-bootstrap/README.md) | 단일 노드 k3s Ansible 구성 | 8 | `NOT_REVALIDATED` |
| [40 Zero Trust Package Contracts](labs/40-zero-trust-package-contracts/README.md) | 보안 패키지·검증·롤백 계약 | 38 | `NOT_REVALIDATED` |

**참고:** 원본 저장소의 파일 경로 목록은 완전한 소스 백업이 아니며, 일부 영역은 보안·출처·중복 우려로 미이관 상태입니다. [남은 원본 영역](docs/migration/remaining-source-areas.md)을 확인하세요.

### Additional extracted labs (41–48)

| 랩 | 재사용 범위 | 출처 | 이관 소스 파일 |
|---|---|---|---:|
| [41 Dandelion Restic Recovery](labs/41-dandelion-restic-recovery/README.md) | 다중 서비스 Restic 복구 시나리오 | Team Dandelion | 5 |
| [42 Dandelion Health Triage](labs/42-dandelion-health-triage/README.md) | Web·DB·Proxy 상태 점검·자동복구 위험 분리 | Team Dandelion | 9 |
| [43 Dandelion Service Topology](labs/43-dandelion-service-topology/README.md) | OpenStack·HAProxy·WordPress·MariaDB 설계 | Team Dandelion | 8 |
| [44 OpenStack Observability Deployment](labs/44-openstack-observability-deployment/README.md) | Terraform·Ansible·mTLS 모니터링 배포 소스 | snsd-multicloud-ops | 37 |
| [45 Remote Read-Only Validation](labs/45-remote-readonly-validation/README.md) | EVE-NG·라우터·OpenStack 검증 및 증적 | snsd-multicloud-ops | 33 |
| [46 Zero Trust Target Architecture](labs/46-zero-trust-target-architecture/README.md) | 아키텍처·수용 기준·의존성 | snsd-multicloud-ops | 23 |
| [47 Repository Quality Gates](labs/47-repository-quality-gates/README.md) | CI 검증·리뷰·문서 자동화 | Team Dandelion | 8 |
| [48 Restic Restore & Maintenance](labs/48-restic-restore-maintenance/README.md) | 복원·유지보수·systemd 타이머 | snsd-multicloud-ops | 19 |

새 랩은 모두 `NOT_REVALIDATED`입니다. [41–48 이관 기록](docs/migration/new-labs-41-48.md)과 [Dandelion 원본 파일 목록](docs/migration/dandelion-source-file-manifest.tsv)을 참고하세요. 원본 저장소는 삭제하지 않았습니다.

## 문서 구조

| 문서 | 역할 |
|---|---|
| [누적 브리핑 모음](docs/briefings/README.md) | 분야별 종합·최근 후속·컨퍼런스·출처와 다음 학습 |
| [뉴스 → 기술 실습](docs/news-to-labs.md) | 원문, 발행일, 내 질문, 실행 증적, 미검증 범위의 권위 기록 |
| [기술 흐름](docs/industry-trends.md) | 브리핑에서 반복되는 산업·운영 문제의 분류 |
| [실습 로드맵](docs/lab-roadmap.md) | 실습 순서, 상태, 완료 기준 |
| [커리어 로드맵](docs/career-roadmap.md) | 네트워크 기반에서 클라우드·보안·AI 인프라로 확장하는 순서 |
| [프로젝트 연결](docs/project-map.md) | 독립 실습과 `snsd-multicloud-ops`의 역할·상태 경계 |
| [업데이트 기록](docs/update-log.md) | 날짜별 변경과 검증 결과 |

## 저장소 역할

```text
main/
├─ docs/           근거·로드맵·출처·실습 이관 대장
├─ labs/01-14/     기존에 로컬 검증된 독립 실습
└─ labs/15-48/     3개 프로젝트 저장소에서 선별 이관한 미재검증 랩
```

이 저장소는 단일 **실습 저장소**입니다. 기존 프로젝트 저장소의 유용한 코드와 설계 자료는 소규모 독립 랩으로 옮기고, 앞으로 검증된 랩들을 조합해 새 프로젝트를 설계합니다. 연결된 프로젝트들의 종전 구현·검증 상태를 이관된 랩에 그대로 부여하지 않습니다.

- 신규 랩은 `MIGRATED / NOT_REVALIDATED`에서 출발합니다.
- **실습 축적 → 정상·거부·장애·복구 검증 → 공통 인터페이스 정리 → 조합형 프로젝트 설계** 순서를 따릅니다.
- 삭제 대상 원본 저장소의 Git 히스토리·기여자 기록·고유 문서·미이관 코드는 별도 미러 백업 후 확인해야 합니다. 선별 이관만으로 원본 전체를 보존한 것은 아닙니다.
- [저장소·프로젝트 연결 지도](docs/project-map.md), [이관 대장](docs/migration-register.md)를 기준으로 관리합니다.

## 기록 원칙

- 원문 링크와 발행일을 확인하고, 별도 사건일이 확인된 경우에만 사건일을 기록합니다.
- **계획 / 설계 / 로컬 검증 / 런타임 검증**을 구분합니다.
- 합성 데이터·계정·자산은 실제 데이터와 구분합니다.
- 실제 자격증명, 계정 식별자, 고객 정보, 원시 운영 로그는 저장하지 않습니다.
- 서브 프로젝트의 구현 상태를 이 저장소에서 임의로 승격하지 않습니다.

