# IDC Monitoring & Observability

[FRRouting 기준선](../../01-network-fabric/idc/README.md)을 먼저 확인합니다. 같은 Linux VM에서 Exporter가 FRR VTY와 커널 FIB·포트 카운터를 읽고, Host1에서 L2/L3 HTTP를 확인합니다. FRR·작업 이벤트는 RFC 5424 Syslog로 전송합니다. Grafana는 Prometheus와 Loki를 함께 조회합니다.

## 실행

Linux Docker Engine과 Compose 플러그인을 사용합니다. 컨테이너는 Linux 호스트 네트워크를 공유하고 서비스는 루프백에서 수신합니다.

```bash
export COMPOSE_FILE=labs/role-groups/05-observability-sre/idc/compose.yaml
read -rsp 'Grafana admin password: ' IDC_GRAFANA_PASSWORD
printf '\n'
export IDC_GRAFANA_PASSWORD
docker compose config --quiet
docker compose up -d
docker compose ps
curl -fsS http://127.0.0.1:19090/-/ready
curl -fsS http://127.0.0.1:13100/ready
curl -fsS http://127.0.0.1:13000/api/health
```

Loki와 Alloy가 준비되면 다른 터미널에서 Exporter를 시작합니다. Exporter는 실행할 때 FRR 로그 파일을 처음부터 읽습니다.

```sh
curl -fsS http://127.0.0.1:12346/-/ready
sudo python3 tools/idc.py observe
```

Grafana에서 `admin`과 지정한 비밀번호로 로그인해 **IDC Network Resilience**를 엽니다. 비밀번호는 첫 기동 시 Grafana 데이터에 저장됩니다. 원격 VM이면 필요한 로컬 포트를 SSH로 전달해 조회합니다.

| 엔드포인트 | 용도 |
|---|---|
| `127.0.0.1:13000` | Grafana 대시보드 |
| `127.0.0.1:19090` | Prometheus |
| `127.0.0.1:19093` | Alertmanager |
| `127.0.0.1:13100` | Loki |
| `127.0.0.1:1514/udp` | Alloy Syslog |
| `127.0.0.1:19808` | Exporter와 로컬 Alertmanager 웹훅 |

## 이벤트 상관분석

포트·BGP 이벤트를 링크별 사건으로 생성하고 **IDC Incident Correlation** 대시보드에 게시할 수 있습니다. [사건 수집과 판정](../../01-network-fabric/idc/docs/incident-analysis.md)

```sh
sudo python3 tools/idc.py drill routing-policy --observe 16
```

1. Grafana 시간을 보고서의 `fault_at`과 `restore_at`을 포함하도록 UTC로 지정합니다.
2. `idc_link_oper_up`와 `idc_bgp_peer_up`을 먼저 보고 `idc_ecmp_nexthops`와 `idc_service_probe_success`를 대조합니다. 트래픽은 `rate(idc_interface_rx_bytes_total[30s]) * 8`과 TX의 같은 식으로 bps를 봅니다.
3. Loki Explore에서 `{job="idc-syslog",app="operator"}`를 조회하고 보고서의 실행 ID로 좁힙니다. 같은 시간창의 `app="frr"`와 `app="alertmanager"`를 장비·이웃·알림 이름으로 대조합니다.
4. `.runtime/idc/alerts.jsonl`에서 `firing`·`resolved`를 확인합니다. 링크, BGP, FIB, HTTP의 관계는 [운영 의존성](../../01-network-fabric/idc/architecture.md#운영-의존성)에 있습니다.

Exporter는 장비 질의 실패를 `idc_query_success=0`으로 표시합니다. 포트 Down과 BGP Down은 성공한 질의에서 판정합니다. 2초 스크레이프와 알림 유지 조건 때문에 짧은 경로 변화는 [장애 재현기의 250 ms 목표 샘플](../../07-recovery-dr/idc/README.md#측정-기준)에서 확인합니다. Syslog와 웹훅의 상관관계는 시간·장비·이벤트 유형을 사용하며, 작업 이벤트는 실행 ID로 재조회할 수 있습니다.

`docker compose down`으로 스택을 정리하고 Exporter 터미널에서 Ctrl+C를 누릅니다. [수집·알림 검증 결과](../../07-recovery-dr/idc/validation.md#관제와-자동화)
