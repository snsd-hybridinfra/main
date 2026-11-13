# 프로젝트 연결 지도

기준 저장소는 `snsd-hybridinfra/main`입니다. [7개 운영 랩](../README.md)은 독립적으로 탐색하고, 같은 운영 질문에 필요한 실험은 입력·출력과 증적을 공유해 연결합니다.

| 연결 | 운영 질문 |
|---|---|
| 네트워크 패브릭 · 관측 · 변경 자동화 · 복구 | IDC 장애 시 BGP·FIB·서비스 상태로 영향 범위를 좁히고 원복 결과를 어떻게 검증하는가? [가상 IDC 설계](../labs/role-groups/01-network-fabric/idc/architecture.md) |
| 클라우드 인프라 · 보안 · 플랫폼 배포 | 주소와 권한을 어떻게 사전 검사하고 배포에 필요한 조건을 어떻게 판정하는가? [클라우드 실험](../labs/role-groups/02-cloud-foundation/README.md) · [보안 실험](../labs/role-groups/04-security-trust/README.md) · [플랫폼 실험](../labs/role-groups/03-platform-delivery/README.md) |

[이관 대장](migration-register.md)은 과거 실험 번호와 출처를 기록합니다. [실행 가이드](../labs/role-groups/README.md)에서 기존 로컬 검증과 이관 자료의 범위를 확인할 수 있습니다.
