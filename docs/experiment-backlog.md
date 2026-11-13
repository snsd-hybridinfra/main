# 다음에 추가할 실험

7개 랩의 기존 구성과 검증 도구를 사용해 운영 판단을 한 가지씩 확인합니다. 아래 항목은 후보이며, 각 실험 README에 실행 환경과 결과가 기록되면 상태를 갱신합니다.

| 순서 | 후보 · 연결 랩 | 운영 질문 | 완료 기준 |
|---|---|---|---|
| 1 | IDC 변경 전후 증적 비교 화면 · [변경 자동화](../labs/role-groups/06-change-automation/README.md), [플랫폼 배포](../labs/role-groups/03-platform-delivery/README.md) | 승인 전에 정상, 회귀, 수집 누락을 화면에서 구분할 수 있는가? | 정상·실패·누락 JSON 3종을 불러와 각 판정의 근거와 원복 절차 링크를 표시한다. [PR #7](https://github.com/snsd-hybridinfra/main/pull/7)의 출력 형식이 확정되면 그 형식에 연결한다. |
| 2 | 중복 IP 장애의 영향 범위 · [관측·장애 분석](../labs/role-groups/05-observability-sre/README.md) | ARP MAC 변화가 실제 중복 IP인지 계획된 게이트웨이 전환인지 구분할 수 있는가? | 동일 IP의 MAC 교대, 정상 전환, 단순 이벤트 중복을 각각 재생해 판정과 근거를 비교한다. [PR #6](https://github.com/snsd-hybridinfra/main/pull/6)의 합성 실험을 출발점으로 쓴다. |
| 3 | 두 EVPN 패브릭의 테넌트 경계 · [네트워크 패브릭](../labs/role-groups/01-network-fabric/README.md) | 경계 장비가 장애 나도 허용된 테넌트 경로와 격리 정책이 유지되는가? | 기존 EVPN 실험에 두 번째 가상 패브릭을 연결하고 허용·거부 통신, 경계 장애 후 경로를 비교한다. [배경 기술 노트](briefings/conference-notes.md) |
| 4 | AIDC 혼잡 구간 재현 · [네트워크 패브릭](../labs/role-groups/01-network-fabric/README.md), [관측·장애 분석](../labs/role-groups/05-observability-sre/README.md) | 공유 링크가 혼잡할 때 처리량과 지연을 함께 봐야 병목을 찾을 수 있는가? | 가상 링크에서 부하 유무를 비교해 처리량·p95 지연·드롭을 기록한다. 컨소시엄의 공개 자료를 활용할 경우 시험 조건과 적용 범위를 함께 남긴다. |

새 브리핑과 기술 자료는 [자료 분류 기준](briefings/research-intake.md)에 따라 기록합니다. 기존 후보와 같은 운영 질문은 근거와 검증 조건을 보강합니다.
