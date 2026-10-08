# News-to-Lab Infrastructure Portfolio

「IT·보안 데일리 브리핑」에서 운영 문제를 찾고, 원문을 확인한 뒤 직접 시험 가능한 기술 질문으로 바꾸는 네트워크·클라우드·보안·AI 인프라 포트폴리오입니다.

```text
브리핑 → 원문 확인 → 기술 질문 → 실습 설계 → 정상·장애·거부 검증 → 증적 → 한계 → 프로젝트 적용
```

기사에 나온 사실과 내가 만든 구현을 분리합니다. 실행하지 않은 구성은 성공으로 적지 않으며, 합성 환경과 실제 런타임을 같은 상태로 표시하지 않습니다.

## 현재 상태

| 구분 | 수량 | 의미 |
|---|---:|---|
| 전체 실습 | 14 | 뉴스에서 도출한 독립 기술 질문 |
| 로컬 검증 | 14 | 코드·컨테이너·합성 모델과 임시 로컬 클러스터에서 직접 실행하고 증적 저장 |
| 설계 | 0 | 실행 증적 없이 설계만 남은 실습 없음 |
| 실제 운영 검증 | 0 | 운영·고객 환경 성과를 주장하지 않음 |

## 실습 카탈로그

### Network & Data Center

| 실습 | 상태 | 확인한 결과 |
|---|---|---|
| [01 BGP/ECMP](labs/01-bgp-ecmp/README.md) | 로컬 검증 | 정상 경로 2개, Spine 장애 후 대체 경로 1개와 ping 3/3 |
| [02 EVPN/VXLAN](labs/02-evpn-vxlan/README.md) | 로컬 검증 | VNI 100·200 내부 통신과 VNI 간 격리 |
| [08 AI DC Network](labs/08-ai-dc-network/README.md) | 로컬 검증 | 20 Mbit/s 가상 병목의 처리량과 부하 중 지연 |
| [09 Edge Load Balancer HA](labs/09-load-balancer-ha/README.md) | 로컬 검증 | 관리망 SSH 허용, 데이터망 SSH 거부, 백엔드 장애 중 HTTP 유지 |
| [10 Network Digital Twin](labs/10-network-digital-twin/README.md) | 로컬 검증 | Fabric·Sovereign 경로와 AIDC 통합 Control Plane의 환경별 관측 사각지대 계산 |

### Cloud & Automation

| 실습 | 상태 | 확인한 결과 |
|---|---|---|
| [03 RESTCONF/Python](labs/03-restconf-python/README.md) | 로컬 검증 | 합성 장비 RESTCONF·SSH CLI 인터페이스 3개 일치, 인증 실패 거부 |
| [04 IAM/STS](labs/04-iam-sts/README.md) | 로컬 검증 | 신뢰 관계·세션 축소·명시적 거부 7개 정책 판정; AWS/Azure 런타임 대기 |
| [05 Backup & Recovery](labs/05-backup-recovery/README.md) | 로컬 검증 | 합성 서비스 RTO 1.627초, 손실 2건 |
| [12 AI Multi-Region Data Path](labs/12-ai-multiregion-data-path/README.md) | 로컬 검증 | Cold Miss 8건, Warm Hit 8건, Cache 훼손 감지·단일 파일 복구·재검증 |

### Security & Operations

| 실습 | 상태 | 확인한 결과 |
|---|---|---|
| [06 AAA/RADIUS](labs/06-aaa-radius/README.md) | 로컬 검증 | 승인 1건, 거부 2건 |
| [07 AI Agent Security](labs/07-ai-agent-security/README.md) | 로컬 검증 | Agent ID·도구·파일·통신·예산·합성 승인 경계의 허용·거부 |
| [11 Vulnerability Prioritization](labs/11-vulnerability-prioritization/README.md) | 로컬 검증 | KEV·공식 실제 악용·패치 권고를 합성 자산 맥락으로 구분해 우선순위 판정 |
| [13 Kubernetes RBAC](labs/13-kubernetes-rbac/README.md) | 로컬 검증 | ServiceAccount 읽기 허용 2개와 Secret·삭제·Namespace 밖·ClusterRole 거부 4개 |
| [14 Terraform Security Validation](labs/14-terraform-security-validation/README.md) | 로컬 검증 | 공개 SSH 1건 탐지, CIDR 수정 후 같은 Checkov 규칙 통과 |

## 문서 구조

| 문서 | 역할 |
|---|---|
| [뉴스 → 기술 실습](docs/news-to-labs.md) | 원문, 발행일, 내 질문, 실행 증적, 미검증 범위의 권위 기록 |
| [기술 흐름](docs/industry-trends.md) | 브리핑에서 반복되는 산업·운영 문제의 분류 |
| [실습 로드맵](docs/lab-roadmap.md) | 실습 순서, 상태, 완료 기준 |
| [커리어 로드맵](docs/career-roadmap.md) | 네트워크 기반에서 클라우드·보안·AI 인프라로 확장하는 순서 |
| [프로젝트 연결](docs/project-map.md) | 독립 실습과 `snsd-multicloud-ops`의 역할·상태 경계 |
| [업데이트 기록](docs/update-log.md) | 날짜별 변경과 검증 결과 |

## 저장소 역할

```text
F:\main
├─ docs/   뉴스·로드맵·상태·프로젝트 연결
└─ labs/   독립 재현 실습과 정제 증적

snsd-multicloud-ops
└─ 가상 증권사 Hybrid-Ready Private Cloud IDP 구현
```

이 저장소는 학습·실험의 주 저장소입니다. [snsd-multicloud-ops](https://github.com/snsd-hybirdinfra/snsd-multicloud-ops)는 연결된 구현 프로젝트이며, 실제 상태는 그 저장소의 권위 문서를 따릅니다. 현재 퍼블릭 클라우드 어댑터는 `DEFERRED`, 금융 네트워크는 `DESIGN_ONLY`, 플랫폼 종단 간 런타임은 `NOT_VALIDATED`입니다.

## 기록 원칙

- 원문 링크와 발행일을 확인하고, 별도 사건일이 확인된 경우에만 사건일을 기록합니다.
- **계획 / 설계 / 로컬 검증 / 런타임 검증**을 구분합니다.
- 합성 데이터·계정·자산은 실제 데이터와 구분합니다.
- 실제 자격증명, 계정 식별자, 고객 정보, 원시 운영 로그는 저장하지 않습니다.
- 서브 프로젝트의 구현 상태를 이 저장소에서 임의로 승격하지 않습니다.
