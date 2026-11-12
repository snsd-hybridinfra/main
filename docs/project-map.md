# 프로젝트 연결 지도: Labs First

**기준:** 2026-11-12, `snsd-hybridinfra/main` 검토 브랜치. 이 문서에서 말하는 상태는 새 이관 랩의 현재 상태이며, 원본 프로젝트의 과거 통합 상태가 아닙니다.

## 현재 운영 원칙

```text
Briefings / Research
         ↓
Single-purpose labs (labs/)
         ↓
Local reproducibility + normal/deny/fail/recover evidence
         ↓
Stable inputs, outputs, interfaces and reusable modules
         ↓
Composed projects (only when ready)
```

기존 01~14번은 독립 로컬 검증 자료를 가진 실습이며, 15~48번은 원본을 선별 이관·재구성한 **미재검증** 랩입니다. 과거 프로젝트를 옮겨왔다고 새 랩이 통합 완료되는 것은 아닙니다.

## 활용 가능한 랩군

| 범위 | 핵심 소재 | 재사용 목적 |
|---|---|---|
| [01 BGP/ECMP](../labs/01-bgp-ecmp/README.md), [02 EVPN/VXLAN](../labs/02-evpn-vxlan/README.md), [10 Digital Twin](../labs/10-network-digital-twin/README.md) | 경로, Overlay, 변경 전 검증 | 네트워크 기능·경로 모델링 |
| [03 RESTCONF/Python](../labs/03-restconf-python/README.md), [05 Backup/Recovery](../labs/05-backup-recovery/README.md), [06 AAA/RADIUS](../labs/06-aaa-radius/README.md) | 자동화, 복원, 접근 제어 | Day-2 운영과 장애 대응 |
| [13 Kubernetes RBAC](../labs/13-kubernetes-rbac/README.md), [14 Terraform Validation](../labs/14-terraform-security-validation/README.md) | 최소 권한, 코드 정책 검사 | 배포 전후 보안 게이트 |
| [15 AWS VPC/Ansible](../labs/15-aws-2tier-vpc/README.md) | AWS 네트워크·Bastion·ALB 자동화 | Public cloud 네트워크 구성, 재검증 대기 |
| [16 OpenStack/Ansible Ops](../labs/16-openstack-ansible-operations/README.md) | Private IaaS와 운영 체크 | 자동화와 운영 Runbook, 재검증 대기 |
| [17 Cloud Network & Access Guardrails](../labs/17-cloud-network-access-baselines/README.md) | OpenStack 네트워크 Terraform, Kubernetes RBAC | 보안 정책·IaC 기반선, 재검증 대기 |
| [18 Bounded Observability](../labs/18-sanitized-observability/README.md) | Loki, Alloy, Grafana | 합성 운영 이벤트 수집과 시각화, 재검증 대기 |
| [19 Metric Anomaly Scoring](../labs/19-metric-anomaly-scoring/README.md) | 합성 메트릭 처리·임계값 점수 | 이상징후 기록·인적 검토, 재검증 대기 |
| [20 PostgreSQL Restic Verification](../labs/20-postgres-restic-verification/README.md) | PostgreSQL dump·Restic·무결성 검증 | DR 사전검증 설계, 재검증 대기 |

## 추가 이관 랩 21–48

| 랩군 | 관심사 |
|---|---|
| 21–22 | 변경 승인, 증적 유효성, 반복·회귀 검증 |
| 23–25 | FinOps, 멀티클라우드 IaC, 공급망 |
| 26, 33 | 서비스 관측, EVE-NG 검증 |
| 27–29 | 신청, 승인·권한, Terraform 프로비저닝 원본 |
| 30–32 | AI Agent/NAS 계약, GitOps, 보안 기준선 |

| 34–35 | PostgreSQL 스키마·마이그레이션, 사용자·관리자 포털 UI 셸 |
| 36–37 | Day-2 운영 Runbook과 원본 검증 테스트 |
| 38–40 | Identity/Device, k3s Ansible, Zero Trust 패키지 계약 |

| 41–43 | Team Dandelion의 Restic·상태 점검·서비스 토폴로지 참고자료 |
| 44–46 | OpenStack 모니터링 배포, 원격 읽기 전용 검증, Zero Trust 아키텍처 |
| 47–48 | Team Dandelion의 저장소 품질 검증과 IDP 복구·유지보수 참고자료 |

**모두 이관·재검증 대기**입니다. 특히 API·공급망·클러스터 소스는 단독 실행 가능한 완성 랩이라는 의미가 아닙니다.

## 출처와 보존

- 세 원본 저장소의 정확한 소스 커밋과 선별 파일 수: [이관 대장](migration-register.md)
- 이관하지 않은 코드·문서·기여 기록은 **저절로 보존된 것이 아닙니다.** 원본 삭제 전 Git 미러·별도 GitHub 메타데이터 백업을 확인합니다.
- 원본 `snsd-multicloud-ops`의 과거 IDP 구현 상태, 통합 영역과 14개 독립 랩의 연결표는 [역사적 연결표](archive/legacy-project-map-2026-11.md)로 분리했습니다. 과거 설명을 신규 랩의 현재 상태로 오인하면 안 됩니다.

## 향후 조합형 프로젝트

1. 각 랩의 전제 조건, 입력/출력, 재현 명령을 문서화합니다.
2. 정상·거부·장애·복구를 실험하고 정제된 증적을 저장합니다.
3. 목적에 맞는 2개 이상 랩의 인터페이스를 연결해 설계합니다.
4. 통합 테스트 및 복구·운영 Runbook을 별도로 검증합니다.
5. 통합 성과를 따로 발표하고, 출처가 다른 팀 프로젝트 기여는 적절히 표시합니다.

고객사 운영망에서 추출한 실설정, 인증정보, 로그 및 내부 주소는 포함하지 않습니다.
