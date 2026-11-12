# IDC Failure Analysis

[패브릭 기준선](../../01-network-fabric/idc/README.md)을 확인한 VM에서 장애를 한 건씩 실행합니다. [실측 보고서](validation.md) · [장애처리 양식](incident-template.md)

```sh
for fault in spine-link bgp-neighbor ecmp-path leaf-device routing-policy; do
  sudo python3 tools/idc.py drill "$fault" || break
done
```

| 시나리오 | 장애 주입 | 장애 시 확인 |
|---|---|---|
| `spine-link` | Leaf1의 U1 링크 Down | U1 이웃 Down, FIB 2→1, 대체 Spine으로 HTTP |
| `bgp-neighbor` | U1 IPv4 eBGP 이웃 관리 종료 | 링크 UP, 해당 이웃 Down, FIB 2→1 |
| `ecmp-path` | Leaf1의 IPv4 최대 경로 2→1 | 양쪽 IPv4 이웃 Established, FIB 2→1 |
| `leaf-device` | Leaf2의 세 포트 Down과 FRR 프로세스 종료 | Leaf2 연결 상실, FIB 2→0, 단일 연결된 Host2 서비스 중단 |
| `routing-policy` | 양쪽 Spine에서 수신하는 VTEP /32를 Leaf1에서 필터링 | U1 링크와 IPv4 이웃 정상, FIB 2→0, HTTP 중단 |

기본 장애 관측창은 12초입니다. `--observe`와 `--recovery`로 관측창과 기준선 대기 상한을 조정할 수 있습니다. 각 시나리오는 자동으로 역변경을 실행한 뒤 같은 기준선으로 검증합니다. 예외가 발생하면 해당 실행의 보고서를 확인합니다.

## 측정 기준

- UTC는 장애·원복 명령 시작과 작업 이벤트의 상관분석에 사용합니다. 소요 시간은 단조 시계로 계산합니다.
- FIB·ICMP·HTTP를 각각 250 ms 목표 간격으로 샘플링합니다. 명령 지연에 따라 실제 간격이 달라지며 `samples.csv`에서 확인합니다.
- FIB 수렴은 장애 명령 시작부터 기대 next hop 개수가 연속 3회 관측된 구간의 첫 샘플까지입니다. 원복 수렴은 기준선 next hop 집합의 연속 3회 관측을 사용합니다.
- 패킷 손실은 장애 구간에서 유효하게 실행된 L3 ICMP의 실패 수와 전체 시도 수입니다. 실행 오류 건수는 별도로 표시합니다.
- HTTP 중단은 첫 실패부터 연속 3회 정상 중 첫 샘플까지입니다. 원복 후 회복은 원복 명령 시각부터 같은 정상 샘플까지입니다. 관측된 중단이 없으면 미관측으로 표시합니다.

`.runtime/idc/drills/<실행 ID>/`에 `result.json`, `samples.csv`, `timeline.jsonl`, `frr/*.log`와 `REPORT.md`가 저장됩니다. 같은 실행 시간창의 [관제 지표·로그·알림](../../05-observability-sre/idc/README.md#이벤트-상관분석)을 추가로 대조합니다.
