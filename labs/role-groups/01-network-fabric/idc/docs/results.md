# IDC 장애 상관분석과 변경 검증 결과

2026-11-13 KST · 격리 Debian 13 QEMU VM · Linux 6.12.116+deb13-amd64 · FRRouting 10.3 · Ansible Core 2.19.11.

Spine 2대·Leaf 2대·Host 2대에서 IPv4·EVPN BGP 이웃 상태 16개, 양쪽 Leaf의 VTEP next hop 2개, ICMP와 L2/L3 HTTP 기준선을 확인했습니다. 종료 후 네임스페이스를 정리했습니다.

## 장애 재현

| 시나리오 | 첫 이벤트 탐지 (초) | FIB 수렴 (초) | ICMP 손실 | 원복 명령 후 HTTP (초) | 관측 |
|---|---:|---:|---:|---:|---|
| Spine–Leaf 링크 | 0.026 | 0.198 | 0/50 | 미관측 | U1의 포트·BGP Down 한 사건, ECMP 2→1 |
| BGP Neighbor | 0.092 | 0.464 | 1/51 | 미관측 | 링크 UP, BGP Down 한 사건, 원인 불확실 |
| 라우팅 정책 | 미관측 | 0.403 | 51/52 | 0.788 | IPv4 BGP 유지, VTEP 경로·HTTP 실패 |
| Leaf 장비 | 0.017 | 1.161 | 52/52 | 8.614 | U2·U4·H2의 사건 3건, Host2 서비스 중단 |

첫 이벤트 탐지는 장애 주입 명령부터 사건에 포함된 첫 Exporter 또는 FRR 이벤트까지입니다. FIB와 HTTP는 250 ms 목표 프로브로 확인했습니다. 정책 오류는 변경 검증으로 탐지했고, 별도 장애 재현에서 수렴과 회복을 계측했습니다. [계측 기준](../../../07-recovery-dr/idc/README.md#측정-기준)

U1 사건에는 양쪽 장비의 포트·BGP 전이와 동일 장비·포트 범위의 최근 변경 2건이 포함됐습니다. 같은 시간창으로 재분석한 사건 ID가 일치했습니다. [U1 사건 JSON](evidence/link-incident.json)

## 변경 검증

| 후보 | 변경 결과 | 수동 원복 확인 |
|---|---|---|
| Description | PASS · 경로·서비스 유지 | 구성 4개와 기준 상태 일치 |
| 미광고 /32 거부 | PASS · 경로·서비스 유지 | 구성 4개와 기준 상태 일치 |
| 원격 VTEP /32 거부 | FAIL · Leaf1 FIB와 ICMP·HTTP 실패 | 구성 4개와 기준 상태 일치 |

정책 변경 실패 직후에 다시 검사해도 서비스는 실패했습니다. 작업자 명령으로 prefix-list 시퀀스를 제거한 뒤 운영 상태와 원본 구성 SHA-256을 함께 검증했습니다. [전후 상태와 구성 diff](evidence/change-validation.json)

## 관제와 검증 범위

Grafana 13.1.0에서 사건 대시보드 4개 패널을 로드했습니다. Loki 요약 6건은 Grafana 조회에서 고유 사건 5건으로 집계됐습니다. 포트·BGP 알림 웹훅과 변경 검증 실패 로그를 확인했습니다. [시나리오와 관제 관측값](evidence/runtime.json)

Compose 설정을 검사하고 이미지와 동일한 버전의 관제 실행 파일을 VM에서 구동했습니다. Docker Compose 컨테이너 기동과 EVE-NG·Cisco·EOS 런타임 검증은 미실행입니다. [재현 절차](test-scenarios.md) · [기존 IDC 검증](../../../07-recovery-dr/idc/validation.md)
