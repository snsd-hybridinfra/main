# 장애 재현과 테스트

먼저 [FRRouting 기준선](../README.md#frrouting-환경)과 [관제](../../../05-observability-sre/idc/README.md)를 준비합니다. 측정 중에는 시나리오를 한 번에 하나씩 실행합니다.

| 시나리오 | 실행 | 기대 관측 |
|---|---|---|
| Spine–Leaf 링크 | `sudo python3 tools/idc.py drill spine-link` | 포트와 IPv4 BGP Down이 U1 한 사건, ECMP 2→1 |
| BGP Neighbor | `sudo python3 tools/idc.py drill bgp-neighbor` | 링크 UP, BGP Down, ECMP 2→1. 원인은 불확실 |
| 잘못된 라우팅 정책 | `sudo python3 tools/idc.py change-validate apply break-vtep --id policy-01` | FIB·HTTP 실패, 종료 코드 1, 수동 복구 절차 |
| Leaf 장비 | `sudo python3 tools/idc.py drill leaf-device` | Leaf2의 연결과 Host2 서비스 영향 및 회복 |

각 장애 전 UTC를 기록하고 같은 시간창을 분석합니다. `drill`은 장애 해제를 포함합니다. 정책 변경 검증의 원복은 작업자가 `change-validate restore --run-dir .runtime/idc/operations/changes/policy-01`을 실행합니다. 별도로 `drill routing-policy`를 실행하면 동일 정책의 수렴과 복구 시간을 계측합니다. [수집 절차](incident-analysis.md#실행-중인-랩에서-수집) · [계측 정의](../../../07-recovery-dr/idc/README.md#측정-기준)

```sh
python3 -m unittest discover -s tests -v
python3 tools/check_catalog.py
python3 tools/run_role.py all
```

[실제 관측 결과](results.md)
