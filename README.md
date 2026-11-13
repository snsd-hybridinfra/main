# 네트워크·인프라 운영 포트폴리오

금융권 IDC 네트워크 운영 경험을 바탕으로 네트워크, 클라우드, 보안, 장애 대응을 가상 환경에서 실험합니다. 각 랩에서 하나의 운영 영역을 다루고, 개별 실험에는 구성·코드·검증 기록을 함께 둡니다.

| 랩 | 실험 예시 |
|---|---|
| [네트워크 패브릭](labs/role-groups/01-network-fabric/README.md) | BGP/ECMP 경로 전환, EVPN/VXLAN 세그먼트 격리, AIDC 공유 병목 |
| [클라우드 인프라](labs/role-groups/02-cloud-foundation/README.md) | AWS·Azure·OpenStack 주소 계획, Terraform 공개 SSH 탐지, k3s 초기 구성 |
| [플랫폼 배포](labs/role-groups/03-platform-delivery/README.md) | 실험 카탈로그 UI, 셀프서비스 VM 요청, Kubernetes GitOps |
| [보안·접근 제어](labs/role-groups/04-security-trust/README.md) | IAM/STS 세션 권한, AAA/RADIUS 승인·거부, Kubernetes 최소 권한 |
| [관측·장애 분석](labs/role-groups/05-observability-sre/README.md) | Prometheus·Grafana·Loki 장애 추적, 합성 메트릭 이상 탐지, 서비스 상태 분류 |
| [변경 자동화](labs/role-groups/06-change-automation/README.md) | RESTCONF와 CLI 상태 비교, 변경 승인 정책, 회귀 검증 |
| [백업·복구](labs/role-groups/07-recovery-dr/README.md) | 서비스 RTO/RPO 측정, PostgreSQL·Restic 백업 검증, 복원 후 점검 |

## 실행

Linux에서 Python 3.11 이상으로 저장소 루트에서 실행합니다.

```sh
python3 tools/check_catalog.py
python3 tools/run_role.py all
```

첫 명령은 랩 구조와 링크를 검사합니다. 두 번째 명령은 랩마다 로컬 검증 시나리오 하나씩 실행하고 `.runtime/role-labs/<UTC>/summary.json`에 결과를 저장합니다. 개별 실험의 장비·클라우드 실행 조건과 이전 검증 범위는 각 실험 README에서 확인할 수 있습니다.

[실행 기록과 이관 기준](labs/role-groups/README.md) · [학습 순서](docs/lab-roadmap.md)

## 실험 탐색과 기술 기록

[로컬 카탈로그 UI](labs/role-groups/03-platform-delivery/experiments/portfolio-catalog/README.md)에서 키워드·랩·검증 상태로 실험을 찾을 수 있습니다.

[브리핑](docs/briefings/README.md) · [컨소시엄](docs/briefings/research-intake.md#컨소시엄) · [세미나](docs/briefings/research-intake.md#세미나) · [다음 실험 후보](docs/experiment-backlog.md)
