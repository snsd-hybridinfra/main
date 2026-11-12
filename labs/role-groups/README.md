# 실습 카탈로그

7개 역할 페이지에서 대표 실습과 51개 번호 랩의 코드·설계·검증 기록을 찾을 수 있습니다. [대표 IDC 프로젝트](../../README.md)

| 역할 | 먼저 볼 실습 |
|---|---|
| [Network Fabric](01-network-fabric/README.md) | BGP/ECMP·EVPN 경로와 패브릭 구성 검증 |
| [Cloud Foundations](02-cloud-foundation/README.md) | AWS·Azure·OpenStack 주소 배치와 중복 탐지 |
| [Platform Delivery](03-platform-delivery/README.md) | 개발 VM 요청 해석과 배포 조건 확인 |
| [Security & Trust](04-security-trust/README.md) | IAM/STS 신뢰 관계와 권한 판정 |
| [Observability & SRE](05-observability-sre/README.md) | 지표·로그·알림으로 장애 영향 확인 |
| [Change Automation](06-change-automation/README.md) | RESTCONF/CLI 비교, 백업·원복 검증 |
| [Recovery & DR](07-recovery-dr/README.md) | 서비스 장애 주입, 복구 시간 측정 |

## 일괄 실행

Linux에서 Python 3.11 이상으로 저장소 루트에서 실행합니다.

```sh
python3 tools/run_role.py all
```

결과는 `.runtime/role-labs/<UTC>/`에 저장됩니다. [대표 사례 실행 기록](evidence/2026-11-12.json)

## 관련 문서

[역할 구성](../../docs/role-consolidation-plan.md) · [프로젝트 연결 지도](../../docs/project-map.md) · [이관 대장](../../docs/migration-register.md) · [카탈로그 데이터](manifest.json)

[브리핑](../../docs/briefings/README.md) · [뉴스와 실습 매핑](../../docs/news-to-labs.md) · [커리어 로드맵](../../docs/career-roadmap.md)
