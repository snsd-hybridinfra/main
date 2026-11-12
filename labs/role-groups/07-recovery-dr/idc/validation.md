# IDC Network Operations & Resilience 검증 결과

2026-11-12 UTC · QEMU의 격리 Debian 13 Linux VM · Linux 6.12.107 · FRRouting 10.3 · Python 3.13.5.

기준선에서 두 주소 계열의 장비별 이웃 상태 16개가 Established였습니다. 양쪽 Leaf에 원격 VTEP next hop이 2개씩 설치됐고, VNI 1010의 원격 MAC·IMET, L3 VNI 50000과 TENANT의 원격 Type 5 경로를 확인했습니다. 1500바이트 L2 ICMP, L3 ICMP 및 L2/L3 HTTP가 통과했습니다. [기준선 JSON](../../01-network-fabric/idc/evidence/baseline.json)

## 장애 5종

| 장애 | 시작 UTC | FIB 수렴 (초) | 장애 구간 ICMP 손실 | HTTP 중단 (초) | 원복 후 FIB / HTTP (초) |
|---|---|---:|---:|---:|---:|
| Spine–Leaf 링크 | 08:46:05.839 | 0.175 | 0/50 | 미관측 | 0.296 / 미관측 |
| BGP Neighbor | 08:46:26.343 | 0.183 | 1/49 | 미관측 | 2.567 / 미관측 |
| ECMP 경로 | 08:46:47.259 | 0.184 | 0/49 | 미관측 | 0.342 / 미관측 |
| Leaf 장비 | 08:47:05.617 | 1.165 | 52/52 | 20.808 | 6.971 / 8.444 |
| 라우팅 정책 | 08:47:34.031 | 0.421 | 51/52 | 13.227 | 0.391 / 0.616 |

5종 모두 장애 상태와 원복 후 기준선이 기대값에 일치했습니다. ICMP 실행 오류는 0건이었습니다. 링크·BGP·ECMP 사례는 FIB 2→1, Leaf2·정책 사례는 2→0을 관측했습니다. Leaf2 복구 때는 프로세스 재시작과 인접 관계 및 오버레이 재학습이 필요했습니다. 정책 사례에서는 IPv4 이웃과 U1 링크를 유지한 채 VTEP /32가 사라졌습니다.

FIB와 HTTP는 250 ms 목표 샘플링의 연속 3회 판정을 사용했습니다. 수렴 시간은 이 VM과 실제 프로브 간격에 종속됩니다. [장애·원복 시각, 타임라인, 프로브와 FRR 로그 발췌](evidence/drills.json) · [측정 정의](README.md#측정-기준)

## 관제와 자동화

- Prometheus에서 BGP 이웃 16개, 링크 10개, RX/TX 카운터 각 10개, ECMP 2개, HTTP 2개 시계열을 확인했습니다. Loki에서 FRR 이웃 Down/Up, 작업 이벤트와 웹훅 로그를 조회했습니다. 정책 장애와 BGP 이웃 장애로 발생한 알림의 발화·해제를 확인했습니다. Grafana는 데이터 소스 2개와 패널 9개를 로드했습니다. [관제 JSON](../../05-observability-sre/idc/evidence/monitoring.json)
- Ansible Core 2.19.11로 장비 4대를 백업했습니다. 정상 후보와 서비스 영향 후보 모두 원복 후 기준선이 통과했고 Ansible 전후 백업의 파일 해시 4개가 일치했습니다. [설정 diff와 결과 JSON](../../06-change-automation/idc/evidence/change.json)
- NetBox 4.5.0에서 장비 6대, 인터페이스 24개, 케이블 6개와 회선 1개를 포함한 85개 객체를 등록했습니다. 두 번째 적용은 동일 객체 85개를 재사용했습니다. [NetBox JSON](../../01-network-fabric/idc/evidence/netbox.json)

관제는 Compose 구성 검사와 동일 버전 실행 파일의 통합 테스트를 수행했습니다. EVE-NG와 EOS 4.30은 이미지 준비와 CLI 확인 절차, 설정 후보를 제공합니다. [환경별 실행 안내](../../01-network-fabric/idc/README.md)
