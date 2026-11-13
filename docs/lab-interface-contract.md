# 운영 역할 랩 인터페이스

## 공통 실행

저장소 루트의 `python3 tools/run_role.py all`은 7개 대표 실습을 실행합니다. 역할 디렉터리 이름을 인수로 전달하면 해당 실습만 실행합니다. 역할별 증적은 `.runtime/role-labs/<UTC>/<역할>/`에, 전체 결과는 같은 실행의 `summary.json`에 저장됩니다. 하나라도 실패하면 종료 코드 1을 반환합니다.

[카탈로그](../labs/role-groups/manifest.json)는 각 실험의 경로, 소속 랩과 검증 기록 상태를 정의합니다. 실험의 소스와 과거 증적은 해당 디렉터리에서 관리합니다. 새 역할 실습 결과는 실행한 입력과 사례의 범위에 적용합니다.

## IDC에서 사용하는 계약

| 생산자 | 공유 입력·출력 | 소비자 |
|---|---|---|
| Network Fabric | 합성 `topology.json`, 생성 FRR/EOS 설정, NetBox 등록 계획 | 패브릭 실행기, NetBox, 각 역할 |
| 기준선 검증기 | BGP 이웃 상태, Leaf별 FIB와 VNI, ICMP·HTTP 판정 JSON | 변경·복구 |
| 운영 이벤트 | UTC, 실행 ID, 이벤트 종류, 대상 장비 또는 시나리오 | 장애 보고서, Loki |
| 관제 | 포트 상태·바이트, BGP·FIB·HTTP, 질의 성공, 발화·해제 로그 | Grafana, 장애 타임라인 |
| 변경·복구 | 변경 전후 diff, UTC 타임라인, 프로브·FRR 로그, 원복 후 기준선 | 변경 기록, 장애 보고서 |

FRR 구성·원복은 전용 Linux VM의 예약 네임스페이스에 적용합니다. 관제는 같은 VM의 루프백에서 수집합니다. NetBox API 인증은 로컬 셸 환경에서 주입합니다. [운영 의존성](../labs/role-groups/01-network-fabric/idc/architecture.md#운영-의존성)

## 증적

실행 환경, 합성 입력, 명령, 관측값과 종료 상태를 기록합니다. 수렴과 복구 시간은 측정 기준을 함께 남깁니다. 역할 대표 실습은 [공통 실행 결과](../labs/role-groups/evidence/2026-11-12.json)에, IDC 패브릭과 장애·관제·변경·원장은 [검증 보고서](../labs/role-groups/07-recovery-dr/idc/validation.md)에 있습니다.
