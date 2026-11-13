# 기술자료와 행사 출처

세션 소개에서 확인한 주제를 사용했습니다. 발표의 실제 구현과 성능 수치는 별도 발표 자료에서 확인할 사항입니다. 이 랩의 구현과 측정은 [검증 결과](results.md)에 기록했습니다.

| 행사와 날짜 | 세션과 발표자 | 공개된 주제와 실습 적용 |
|---|---|---|
| DATA CENTER KOREA 2026 · 11월 4~6일 KST | 공식 전시 안내 | DCIM 범위의 자산 관리, 운영 자동화, 대시보드. 토폴로지 원장과 관측을 연결했습니다. [전시 안내](https://datacenterkorea.kr/exhibtion/introduce/) |
| DATA CENTER KOREA 2026 · 11월 6일 KST | 「사일로를 넘어 자율화로」 · 차윤경 | 데이터센터 운영 워크플로. 장애 근거와 변경 이력을 한 보고서에서 확인합니다. [공식 프로그램](https://datacenterkorea.kr/conference-overview/) |
| KubeCon + CloudNativeCon North America 2026 · 11월 10일 MST | 「The SRE Is Not Dead」 · Muhammed Yunas Chirayath, Ajmal Ali kannu | 관측 신호와 변경·의존성 맥락. 랩에서는 토폴로지와 변경 시각을 장애에 연결했습니다. [공식 세션](https://events.linuxfoundation.org/kubecon-cloudnativecon-north-america/program/schedule/?id=1250770) |
| KubeCon + CloudNativeCon North America 2026 · 11월 10일 MST | 「When Infrastructure Breaks in Production」 · Priya Namasivayam | 변경 후 인프라 검증 게이트. Ansible의 구성 적용과 Python의 상태 판정을 연결했습니다. [공식 세션](https://events.linuxfoundation.org/kubecon-cloudnativecon-north-america/program/schedule/?id=1246033) |

## 구현 근거

- IPv4·EVPN 이웃, VTEP 경로, soft refresh. [FRR BGP](https://docs.frrouting.org/en/stable-10.3/bgp.html) · [FRR EVPN](https://docs.frrouting.org/en/stable-10.3/evpn.html)
- 경보 규칙, 로그 범위 조회와 사건 ID 집계. [Prometheus 경보](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/) · [Loki API](https://grafana.com/docs/loki/latest/reference/loki-http-api/) · [LogQL 집계](https://grafana.com/docs/loki/latest/query/metric_queries/)
- 인자 배열을 사용하는 로컬 VTY 실행. [Ansible command](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/command_module.html)
- vEOS 공식 이미지·사용 조건. [EVE-NG 설치 가이드](https://www.eve-ng.net/index.php/documentation/howtos/howto-add-arista-veos/) · [Arista EULA](https://www.arista.com/assets/data/pdf/software-agreement/EndUserLicenseAgreement.pdf)
