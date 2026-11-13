# 09 Edge Load Balancer HA: 관리면·사용자망·OT망 분리와 백엔드 장애 복구

## 왜 이 실습을 계속 고쳤는가

처음에는 [F5 BIG-IP APM CVE-2026-94127 권고](https://my.f5.com/manage/s/article/K000162605)와 [CISA의 2026-09-22 KEV 공지](https://www.cisa.gov/news-events/alerts/2026/09/22/cisa-adds-four-known-exploited-vulnerabilities-catalog)를 보고 백엔드 하나가 멈췄을 때 서비스가 유지되는지 확인했다.

그다음 [Citrix NetScaler 보안 공지 CTX697096](https://support.citrix.com/external/article/CTX697096)(2026-09-27), [관리·데이터 Plane 분리 문서](https://docs.netscaler.com/en-us/citrix-adc/current-release/networking/mgmt-and-data-plane-separation.html)(2026-09-08), [Cisco Catalyst SD-WAN Manager 권고](https://sec.cloudapps.cisco.com/security/center/content/CiscoSecurityAdvisory/cisco-sa-sdwan-webauth-xr8beuuU)(2026-09-30)를 보며 관리 SSH를 사용자 트래픽과 분리했다.

[Palo Alto Networks CVE-2026-0322 공지](https://security.paloaltonetworks.com/CVE-2026-0322)(2026-10-14 게시·10-15 갱신)는 인터넷에서 접근 가능한 PAN-OS 관리 인터페이스의 위험이 가장 높고, 신뢰할 수 있는 내부 주소나 Jump Box로 접근을 제한하라고 권고한다. 10월 15일에 이미 실행한 이 랩의 관리망 전용 SSH와 사용자망 SSH 거부 결과를 이 문제와 연결했다. PAN-OS 장비나 해당 CVE를 실행한 것은 아니다.

2026-10-12 프랑스 CERT는 냉장 설비 원격 제어기 침해 경보를 냈다. [AP의 2026-10-14 후속 보도](https://apnews.com/article/france-supermarkets-hacked-cybercrime-81c2d5721f4df77f601f71741ef7c291)는 10월 12일 프랑스 슈퍼마켓 약 700곳에 영향이 있었고, 당국이 VPN 또는 보호된 네트워크를 통해서만 재연결하라고 권고했다고 전했다. 원격 제어기가 업무용 사용자망과 같은 경로에 놓여 있으면 피해 범위가 커질 수 있다는 문제로 읽었다.

로드밸런서, 관리면, OT 격리는 모두 서비스 경계의 접근 경로를 확인하는 질문이라 새 랩을 만들지 않았다. 이 실습은 실제 냉장 장비나 공개된 취약점을 공격하지 않는다. Docker 네트워크 세 개로 다음만 확인한다.

1. SSH 관리 서비스가 관리망 주소에서만 열리는가?
2. 사용자 데이터망과 관리망에서 OT 제어기 주소로 직접 갈 수 없는가?
3. OT 작업자는 OT망 안의 제어기에 접근할 수 있는가?
4. 백엔드 하나가 멈춰도 HTTP 요청이 이어지고, 복구 후 다시 풀에 들어오는가?

## 실습 구성

```text
관리망 172.31.10.0/24
Admin 172.31.10.20 ── SSH ──> Edge 172.31.10.10:22

데이터망 172.31.20.0/24
Client 172.31.20.20 ── HTTP ─> Edge 172.31.20.10:80
                                      ├─ web01 172.31.20.31
                                      └─ web02 172.31.20.32

OT망 172.31.30.0/24
OT Operator 172.31.30.20 ── HTTP ─> OT Controller 172.31.30.30

Client/Admin ──> OT Controller  [직접 접근 거부 기대]
Client ── SSH ──> Edge data IP  [거부 기대]
```

- `edge`: 관리망과 데이터망에 연결된 Nginx·OpenSSH 컨테이너
- `admin`: 관리망에서 일회성 공개키로 SSH를 시도하는 컨테이너
- `client`: 데이터망에서 HTTP, SSH 거부, OT 직접 접근 거부를 확인하는 컨테이너
- `ot-operator`, `ot-controller`: OT망 내부 허용 경로를 확인하는 합성 작업자와 HTTP 제어기
- `web01`, `web02`: 자신의 이름을 반환하는 Nginx 백엔드
- [compose.yaml](compose.yaml): 세 네트워크와 고정 주소 구성
- [run.ps1](run.ps1): 접근 경계와 정상·장애·복구 흐름을 실행하고 JSON 증적 생성

테스트용 개인키는 `admin` 컨테이너 안에서 실행할 때마다 만들고 종료 시 함께 지운다. 비밀번호 로그인은 껐고 저장소에는 개인키를 남기지 않는다.

## 실행

```powershell
./run.ps1
```

스크립트는 빌드와 검증을 마친 뒤 컨테이너와 전용 네트워크를 정리한다.

## 직접 확인한 결과

2026-10-15 재실행의 [통합 JSON 증적](evidence/2026-10-15.json):

| 확인 단계 | 관측 |
|---|---|
| Admin → 관리 주소 SSH | 종료 코드 0, `management-ssh-ok` |
| Client → 데이터 주소 SSH | 연결 실패 |
| OT Operator → OT Controller | 종료 코드 0, `ot-controller-ok` |
| Client → OT Controller | 연결 실패 |
| Admin → OT Controller | 연결 실패 |
| 정상 HTTP | `web01`과 `web02` 모두 응답 |
| `web01` 중단 | `web02` 8/8, 요청 실패 없음 |
| `web01` 복구 | 두 백엔드가 다시 응답 |

이전 [2026-10-01 증적](evidence/2026-10-01.json)은 OT망을 추가하기 전의 관리·데이터망 검증 기록으로 남겼다.

## 이번 실습에서 말할 수 있는 범위

- 세 Docker 네트워크의 소속을 분리했을 때 OT망 내부 접근은 성공하고 관리망·데이터망의 직접 접근은 실패했다.
- 관리 SSH는 관리 주소에서만 성공했고, 사용자 데이터 주소에서는 실패했다.
- Nginx의 passive retry로 단일 백엔드 중단 중 HTTP 응답이 유지되고 복구 후 풀에 다시 들어왔다.
- 프랑스 사고의 냉장 제어기, 펌웨어, 프로토콜, 침해 경로와 공격자는 검증하지 않았다.
- Docker 네트워크는 실제 방화벽·VPN·Jump Host·Identity Proxy·OT 모니터링을 대신하지 않는다. 인터넷 노출, 비상 로컬 제어, TLS, AAA와 성능도 포함하지 않았다.

다음 단계는 허가된 OT 테스트 환경에서 기본 거부 방화벽, VPN 또는 Jump Host 경유 관리, 장비별 허용 목적지, 경보와 비상 수동 제어를 함께 확인하는 것이다.
