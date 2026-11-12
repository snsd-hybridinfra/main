# 운영 역할 랩 구성

메인 저장소는 `snsd-hybridinfra/main`입니다. 51개 번호 랩을 7개 역할에 한 번씩 배정합니다. 역할 페이지는 대표 실습과 관련 소스·기존 증적의 진입점입니다. [역할 랩 인덱스](../labs/role-groups/README.md) · [소유권 목록](../labs/role-groups/manifest.json)

| 역할 | 번호 랩 | 대표 실습 |
|---|---|---|
| Network Fabric | 01, 02, 08, 09, 10, 12, 33, 43 | 경로 모델과 생성된 FRR/EOS 설정을 대조하고 원장 계획 출력 |
| Cloud Foundations | 14, 15, 16, 17, 23, 24, 39, 50, 51 | AWS·Azure·OpenStack 주소 계획과 서브넷 충돌 검증 |
| Platform Delivery | 25, 27, 28, 29, 30, 31, 34, 35, 49 | VM 요청의 카탈로그 해석과 미충족 API 배포 조건 확인 |
| Security & Trust | 04, 06, 07, 11, 13, 32, 38, 40, 46 | IAM/STS 역할 신뢰, 세션 범위, 명시적 거부 판정 |
| Observability & SRE | 18, 19, 26, 42, 44 | 합성 메트릭 검증, 점수화, 보고서 생성 |
| Change Automation | 03, 21, 22, 36, 37, 45, 47 | 인터페이스 읽기 비교와 변경 정책 판정 |
| Recovery & DR | 05, 20, 41, 48 | 로컬 사이트 장애, 백업 누락 거부와 복구 검증 |

## IDC 시나리오 연결

IDC의 Network Fabric·Observability & SRE·Change Automation·Recovery & DR가 하나의 FRR 패브릭을 공유합니다. 패브릭 역할이 제공하는 토폴로지와 기준선을 사용해 관제, 변경, 장애 재현을 같은 가상 서비스에서 실행합니다. 장비·주소·회선 원장은 동일한 토폴로지에서 생성합니다. [의존성 및 토폴로지](../labs/role-groups/01-network-fabric/idc/architecture.md) · [IDC 실측 결과](../labs/role-groups/07-recovery-dr/idc/validation.md)

## 검증

- `python3 tools/check_catalog.py`로 번호 랩 51개와 역할별 링크를 검증합니다.
- `python3 tools/run_role.py all`로 7개 대표 실습을 실행합니다. 공급자 주소·카탈로그·관제 점수 등 대표 실습에서 사용한 부분의 결과는 [실행 증적](../labs/role-groups/evidence/2026-11-12.json)에서 확인합니다.
- FRRouting과 운영 도구의 통합 결과는 실제 실행 환경과 함께 IDC 보고서에 기록합니다. 각 번호 랩의 고유 실행 상태와 출처는 해당 README 및 [이관 대장](migration-register.md)에서 확인합니다.
