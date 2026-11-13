# 네트워크 장애 상관분석

## 수집과 사건 판단

| 입력 | 판정에 쓰는 데이터 |
|---|---|
| Exporter | 성공한 스크레이프에서 포트와 BGP의 Up↔Down 전이 |
| FRR 로그·Loki | 이웃 상태 로그의 장비, 피어, 발생 시각 |
| 토폴로지 | 장비·포트·직접 연결 IPv4 및 EVPN 피어에 해당하는 링크 |
| 변경 이력 | 현재 랩에서 실행한 작업 ID, 시각, 대상 장비와 포트 |

기본 **10초** 안에 같은 링크의 새 증상을 결합합니다. 같은 입력 레코드와 이미 Down인 항목의 반복 알람은 사건 수를 늘리지 않습니다. 링크 포트 Down과 직접 연결 IPv4 BGP Down이 함께 있으면 링크 장애 **의심**으로 표시합니다. BGP만 Down이면 원인은 **불확실**이며, 판단 근거가 된 이벤트 ID를 저장합니다.

사건보다 최대 **5분 앞선** 동일 장비·포트의 변경을 연결합니다. 변경과 장애의 인과관계는 추가 확인이 필요합니다. 사건에 포함된 Down 항목들의 Up을 관측하면 복구로 기록합니다. Leaf 전체 장애는 영향 링크별로 표시합니다.

## 오프라인 재현

```sh
python3 tools/idc.py incident \
  --input labs/role-groups/05-observability-sre/idc/fixtures/link-incident.json \
  --out .runtime/idc/incident-demo
```

[재현 데이터](../../../05-observability-sre/idc/fixtures/link-incident.json) · [사건 JSON 스키마](../../../05-observability-sre/idc/incident.schema.json)

## 실행 중인 랩에서 수집

[관제](../../../05-observability-sre/idc/README.md)를 시작하고 Prometheus의 정상 스크레이프를 확인합니다. 저장소 루트에서 장애 직전의 UTC를 기록합니다.

```sh
since=$(date -u +%FT%TZ)
sudo python3 tools/idc.py drill spine-link
# Loki에서 장애와 복구 로그가 들어온 뒤 조회합니다.
sudo python3 tools/idc.py incident --since "$since" --loki --publish
```

`--until`로 조회 종료 시각을 고정할 수 있습니다. 기본 결과는 `.runtime/idc/operations/incidents/`의 JSON과 Markdown입니다. `--publish`를 사용하면 기존 Alloy/Loki로 사건 요약을 보냅니다. Grafana **IDC Incident Correlation**에서 조회 기간 내 게시된 사건의 고유 ID 수, 포트·BGP 알람과 변경 실패를 확인합니다.

조회는 한 번에 최대 1시간입니다. Loki가 결과 상한에 도달하면 시간창을 줄여 재조회합니다. 짧은 전이, Exporter의 초기 수집 전 장애, Syslog 유실은 수집 범위에 영향을 줍니다. 동일한 사고를 다시 분석할 때는 같은 시간창을 사용합니다.
