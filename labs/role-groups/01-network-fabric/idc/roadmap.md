# IDC 실습 실행 순서

패브릭의 정상 상태를 먼저 확인한 뒤 관제와 장애 시나리오를 실행합니다. EVE-NG/EOS 설정 후보와 확인 명령도 패브릭 가이드에서 볼 수 있습니다. [아키텍처](docs/architecture.md) · [실측 보고서](docs/results.md)

| 순서 | 실습과 확인 기준 |
|---|---|
| 1. [패브릭 준비](README.md) | FRRouting을 실행하고 양쪽 Leaf의 ECMP next hop, EVPN 경로, L2/L3 HTTP 기준선을 확인합니다. |
| 2. [관제 연결](../../05-observability-sre/idc/README.md) | Prometheus 지표, Grafana 대시보드, Loki 로그와 알림을 같은 장애 구간에서 대조합니다. |
| 3. [장애 재현과 상관분석](docs/incident-analysis.md) | U1의 포트·BGP 이벤트를 한 사건으로 묶고 최근 변경을 확인합니다. |
| 4. [백업·변경·원복](docs/change-validation.md) | Ansible 적용 전후와 수동 원복 후 상태를 비교합니다. |
| 5. [NetBox 등록](README.md#netbox-45-인벤토리) | 토폴로지의 포트·주소·회선과 A/Z 종단이 원장과 일치하는지 확인합니다. |

로컬 실행 결과는 `.runtime/idc/`에서 확인합니다. 재실행한 사례의 탐지 시각, 서비스 영향, 원복 근거는 작업 기록에 남길 수 있습니다. [변경 작업 양식](../../06-change-automation/idc/change-template.md) · [장애 처리 양식](../../07-recovery-dr/idc/incident-template.md)
