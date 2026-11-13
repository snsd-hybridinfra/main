# 03 RESTCONF / Python: API와 CLI 상태 대조

## 왜 이걸 확인했는가

[Nokia의 네트워크 자동화 발표](https://www.nokia.com/newsroom/nokia-accelerates-network-automation-through-agentic-unified-data-foundation-with-microsoft/)(2026-09-17)를 보고 자동화가 수집한 상태를 그대로 믿기 전에 다른 관리 경로와 대조해 보고 싶었다. RESTCONF를 선택한 것은 내 실험 설계이며 Nokia·Microsoft 제품을 재현한 것은 아니다.

질문은 간단하다. **같은 장비의 RESTCONF 운영 데이터와 SSH CLI 상태가 인터페이스별로 일치하는가?**

2026-09-22에는 Cisco 공개 샌드박스 두 곳에서 RESTCONF GET이 HTTP 401로 끝나 대조를 진행하지 못했다. 그 실패는 [기존 증적](evidence/2026-09-22.txt)에 그대로 남겨 두었다.

이번에는 외부 계정에 기대지 않고 비교 로직 자체를 끝까지 검증하기 위해 합성 IOS XE 장비를 컨테이너로 만들었다. 상태는 **로컬 검증**이다.

## 로컬 구성

```text
Runner
  ├─ HTTPS GET /restconf/data/...:interfaces
  └─ SSH → show interfaces
              |
              v
     Synthetic IOS XE Device
     ├─ RESTCONF 형식 JSON
     └─ 읽기 전용 합성 CLI
```

- [compare.py](compare.py): RESTCONF와 CLI를 수집하고 인터페이스별 상태를 정규화해 비교
- [compose.yaml](compose.yaml): 외부 포트를 열지 않는 전용 Docker 네트워크
- [device_server.py](device_server.py): Basic 인증을 사용하는 읽기 전용 HTTPS 엔드포인트
- [mock-cli.sh](mock-cli.sh): `show interfaces`만 응답하는 합성 SSH 셸
- [fixtures](fixtures/interfaces.json): API와 CLI에 사용한 고정 인터페이스 상태
- [run.ps1](run.ps1): 임시 비밀번호 생성, 정상·거부 경로 실행, JSON 증적 작성과 정리

자체 서명 인증서를 허용하는 `--local-insecure-tls`는 `device`, `localhost`, `127.0.0.1`에만 사용할 수 있게 제한했다. 실제 장비는 기본 인증서 검증이나 `--ca-bundle`을 사용한다.

## 실행

```powershell
./run.ps1
```

비밀번호와 인증서는 실행할 때마다 새로 만들며 저장소에 남기지 않는다. 실행이 끝나면 컨테이너와 전용 네트워크를 정리한다.

## 직접 확인한 결과

2026-09-29 실행의 [JSON 증적](evidence/2026-09-29.json):

| 확인 | 결과 |
|---|---|
| RESTCONF 수집 | 합성 인터페이스 3개 |
| SSH CLI 수집 | 합성 인터페이스 3개 |
| 공통 인터페이스 대조 | 3개 |
| 상태 불일치 | 0개 |
| API 또는 CLI 한쪽에만 있는 이름 | 0개 |
| 틀린 비밀번호 | HTTP 401, 비교 미실행, 종료 코드 2 |

`GigabitEthernet1`, `GigabitEthernet2`, `Loopback0`의 관리·운영 상태가 두 관리 경로에서 모두 일치했다. 인증 실패 시에는 CLI까지 진행하지 않고 성공 증적도 만들지 않았다.

## 확인하지 않은 범위

- 실제 Cisco IOS XE 장비와 Nokia·Microsoft 제품
- 변하는 실제 장비에서 거의 동시에 수집한 API·CLI 상태
- 운영 인증서 체인, AAA, 구성 변경, Telemetry
- 개인 프로젝트 장비와의 통합

다음 실제 검증은 허가된 IOS XE 가상 장비나 예약형 샌드박스에서 같은 `compare.py`를 실행하고, 주소와 원시 구성을 제거한 대조 결과만 증적으로 남기는 것이다.
