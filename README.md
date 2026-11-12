# Infrastructure Operations Labs

네트워크·클라우드·보안 인프라의 구성, 관제, 변경, 복구를 가상 환경에서 재현하는 포트폴리오입니다. 7개 역할 랩에서 실습을 시작하고, 설계 근거와 증적은 51개 번호 랩과 운영 문서에서 확인할 수 있습니다.

## 시작하기

Linux에서 Python 3.11 이상으로 저장소 루트에서 실행합니다. 복구 실습은 임시 SQLite와 루프백 HTTP를 사용합니다.

```sh
python3 tools/run_role.py all
```

실행별 판정과 증적은 `.runtime/role-labs/<UTC>/`에 저장됩니다. [역할 랩 검증 결과](labs/role-groups/evidence/2026-11-12.json)

## 역할 랩

| 역할 | 바로 확인할 실습 | 참고 랩 |
|---|---|---:|
| [Network Fabric](labs/role-groups/01-network-fabric/README.md) | 패브릭 경로 계산, BGP/ECMP, EVPN/VXLAN, IPAM | 8 |
| [Cloud Foundations](labs/role-groups/02-cloud-foundation/README.md) | AWS·Azure·OpenStack 주소 배치와 중복 탐지 | 9 |
| [Platform Delivery](labs/role-groups/03-platform-delivery/README.md) | 개발 VM 요청 해석, 미충족 배포 의존성 확인 | 9 |
| [Security & Trust](labs/role-groups/04-security-trust/README.md) | IAM/STS 신뢰 정책과 세션 권한·명시적 거부 | 9 |
| [Observability & SRE](labs/role-groups/05-observability-sre/README.md) | 합성 메트릭 이상 탐지, IDC 지표·Syslog·알림 상관분석 | 5 |
| [Change Automation](labs/role-groups/06-change-automation/README.md) | RESTCONF/CLI 정합성, 설정 백업, 변경 검증·원복 | 7 |
| [Recovery & DR](labs/role-groups/07-recovery-dr/README.md) | 네트워크 장애 5종과 로컬 서비스 복구 계측 | 4 |

## IDC Network Operations & Resilience Lab

Spine 2대, Leaf 2대, Host 2대에서 eBGP 언더레이와 EVPN/VXLAN 오버레이를 구성합니다. 동일 토폴로지에서 정상 경로, 장애, 알림, 설정 원복 및 NetBox 원장을 대조합니다. [아키텍처와 토폴로지](labs/role-groups/01-network-fabric/idc/architecture.md) · [검증 결과](labs/role-groups/07-recovery-dr/idc/validation.md)

| 단계 | 실습과 산출물 |
|---|---|
| 1. Network Foundation | [FRRouting 실행, EOS 구성, 정상 경로 검증](labs/role-groups/01-network-fabric/idc/README.md) |
| 2. Monitoring & Observability | [Prometheus, Grafana, Loki/Alloy 및 Alertmanager](labs/role-groups/05-observability-sre/idc/README.md) |
| 3. Failure Analysis | [장애 5종, 손실·수렴·복구 측정과 보고서](labs/role-groups/07-recovery-dr/idc/README.md) |
| 4. Network Automation | [Ansible 설정 백업, Python 변경 검증과 원복](labs/role-groups/06-change-automation/idc/README.md) |
| 5. DCIM & Documentation | [NetBox 등록, 변경·장애 양식과 학습 로드맵](labs/role-groups/01-network-fabric/idc/roadmap.md) |

## 참고 자료

- 51개 번호 랩의 출처와 검증 상태는 [역할 랩 인덱스](labs/role-groups/README.md)에서 확인합니다.
- `snsd-multicloud-ops`의 역할과 이관 범위는 [프로젝트 연결 지도](docs/project-map.md)와 [이관 대장](docs/migration-register.md)에 기록했습니다.
- 브리핑에서 실습으로 이어진 근거와 학습 순서는 [브리핑](docs/briefings/README.md), [뉴스와 실습 매핑](docs/news-to-labs.md), [커리어 로드맵](docs/career-roadmap.md)에 정리했습니다.
