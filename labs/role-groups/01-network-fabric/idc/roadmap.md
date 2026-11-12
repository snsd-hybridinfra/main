# IDC 실습 체크리스트

| 단계 | 직접 확인할 기준 | 결과물 |
|---|---|---|
| 1. 패브릭 구성 | Leaf의 원격 VTEP FIB 2개, EVPN Type 2/3과 Type 5, 두 HTTP 경로 | [설정과 실행 가이드](README.md), `baseline.json` |
| 2. 관제 연결 | 링크·BGP·트래픽·HTTP 지표, 같은 시간창의 Syslog와 알림 | [수집 설정과 대시보드](../../05-observability-sre/idc/README.md) |
| 3. 장애 재현 | 정상과 장애 상태를 비교하고 FIB·ICMP·HTTP로 복구를 판정 | [시나리오와 복구 보고서](../../07-recovery-dr/idc/README.md) |
| 4. 변경 자동화 | 설정 diff, 변경 중 상태 검증, 원복 후 설정과 서비스 비교 | [백업과 변경 절차](../../06-change-automation/idc/README.md), [변경작업 양식](../../06-change-automation/idc/change-template.md) |
| 5. 원장과 정리 | 토폴로지의 포트·주소·회선을 NetBox에서 대조하고 증적을 문서에 연결 | [NetBox 적용 가이드](README.md#netbox-45-인벤토리), [장애처리 양식](../../07-recovery-dr/idc/incident-template.md) |

## 실무 학습 순서

1. 양쪽 Leaf에서 VTEP의 BGP 경로와 실제 FIB를 대조하고 ECMP가 1개로 바뀌는 조건을 설명합니다.
2. 공통 VLAN의 L2 통신과 VRF를 경유하는 서로 다른 VLAN의 L3 통신을 확인합니다. VLAN/VNI·RD/RT·VTEP와 각 EVPN 타입의 역할을 그림에 표시합니다.
3. 포트와 이웃이 모두 올라온 상태에서 HTTP가 멈춘 경우의 진단 순서를 작성합니다. 원격 루프백, 수신 정책, VRF 경로, 로그를 차례로 비교합니다.
4. [측정 결과](../../07-recovery-dr/idc/validation.md)의 장애 사례 하나를 재실행해 탐지 시각, 영향, 원복, 확인 근거를 한 페이지에 기록합니다.
5. 변경 양식에 원복 조건과 적용 전후 증적을 채웁니다. 원장 회선의 A/Z 종단을 기준으로 영향 구간을 설명합니다.

## 파일 찾기

| 경로 | 역할 |
|---|---|
| `tools/idc.py` | 렌더링, 패브릭, 관제, 변경, 복구, 원장 실행 |
| `labs/role-groups/01-network-fabric/idc/` | 공유 토폴로지, FRR/EOS 설정, 검증기, NetBox |
| `labs/role-groups/05-observability-sre/idc/` | Exporter, Compose, Prometheus, Grafana, Loki, Alloy, Alertmanager |
| `labs/role-groups/06-change-automation/idc/` | Ansible 백업, 변경 전후 비교와 원복 |
| `labs/role-groups/07-recovery-dr/idc/` | 장애 주입, 복구 계측, 검증 보고서 |
| `.runtime/idc/` | 재실행 시 로컬에 생성되는 원시 증적 |
