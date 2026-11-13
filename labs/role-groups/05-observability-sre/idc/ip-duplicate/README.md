# IDC IP 중복 탐지: 오프라인 검증

기존 IDC Network Operations & Resilience Lab의 **Observability & SRE**에 포함되는 읽기 전용 PoC입니다. 현재 Cisco/Arista 장비, Genian NAC, 실제 NMS에는 **연결하지 않습니다**.

## 범위

- 정규화한 ARP sender IP/MAC 관측을 기본 120초 시간창에서 비교
- 비교 키: site + vrf + segment + ip (서로 분리된 L2 도메인은 같은 주소여도 충돌 아님)
- IP_DUPLICATE_SUSPECTED (warning): 같은 L2 도메인에서 동일 IP를 다른 MAC 2개 이상이 광고한 정황
- GATEWAY_IP_UNEXPECTED_MAC (critical): 게이트웨이 기준 MAC 목록 외 MAC 관측. 실제 IP 충돌 **확정**이 아닌 신원 불일치 **의심** 이벤트
- 출력: 로컬 JSON 알람 및 RFC 5424 형식의 Syslog **텍스트 미리보기**만 생성
- 전송 기능, 포트 차단 기능, 스위치 설정 변경 기능 없음

## 실행 (Python 3.11+, 추가 패키지 불필요)

저장소 루트에서 다음 명령을 실행합니다.

    python3 -m unittest discover -s labs/role-groups/05-observability-sre/idc/ip-duplicate -p 'test_*.py' -v

    python3 labs/role-groups/05-observability-sre/idc/ip-duplicate/detect.py \
      --input labs/role-groups/05-observability-sre/idc/ip-duplicate/fixtures/synthetic.json \
      --output .runtime/ip-duplicate/alerts.json \
      --syslog-output .runtime/ip-duplicate/alerts.syslog

    cat .runtime/ip-duplicate/alerts.json

테스트 fixture의 예상 결과: 서버 간 IP 충돌 의심 1건, 게이트웨이 MAC 신원 불일치 의심 1건. GitHub Actions는 관련 경로 변경 PR/push 및 수동 실행 시 동일한 합성 테스트를 수행합니다.

## 검증 경계와 운영 적용 전 체크

1. 이 데이터는 Cisco와 Arista 원본 CLI/Syslog를 파싱한 것이 아니라, 양측 장비에서 관측할 수 있다고 가정하여 **합성한 ARP claim 입력**입니다. 실제 관측 경로와 권한 확인이 선행되어야 합니다.
2. ARP 테이블의 스냅샷이나 MAC FDB만으로는 서버 간 실시간 중복을 보장할 수 없습니다. SPAN/TAP도 사전 승인 없이 설정하지 않습니다.
3. EVPN 브리지 도메인, HSRP/VRRP/VARP, anycast, Proxy ARP, VM 이동, L2 도메인 식별, 수집 누락/지연과 시계 동기화를 따로 검증해야 합니다.
4. 수집 방식과 오탐 검증, MAC 예외 기준, NMS의 Syslog/API 수신 방식은 아직 구현하지 않았습니다.
5. 이 단계에서 모든 중복 IP를 탐지한다고 주장하지 않습니다. 알람은 조사 대상일 뿐 자동 조치의 근거가 아닙니다.

**기밀:** 문서 전용 192.0.2.0/24와 임의의 로컬 관리 MAC만 사용합니다. 실서버 IP/MAC, 내부 장비명, 고객망 구성, 운영 로그를 GitHub에 커밋하지 않습니다.
