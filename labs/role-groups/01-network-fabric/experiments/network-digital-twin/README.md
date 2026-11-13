# Network Digital Twin: 애플리케이션 경로·AIDC Control Plane 의도 검증

## 이걸 해본 이유

[IP Fabric의 Application To Infrastructure Mapping 101](https://ipfabric.io/blog/application-to-infrastructure-mapping/)(2026-09-23)은 애플리케이션·워크로드·흐름을 네트워크 모델과 연결해 실제 경로와 세그멘테이션 정책을 확인하는 문제를 다룬다. [IP Fabric 8.1 릴리스 노트](https://docs.ipfabric.io/latest/releases/release_notes/8.1/)에서도 애플리케이션 흐름이 지나는 장비 계산과 클라우드 보안 정책을 반영한 경로 조회 기능을 설명한다.

2026-09-30 브리핑에서 본 [AWS European Sovereign Cloud 독립 운영 시험 발표](https://aws.amazon.com/blogs/security/aws-european-sovereign-cloud-demonstrating-an-independent-operation/)(2026-09-28)도 같은 질문으로 연결됐다. AWS는 2026-10-24에 Global Network Backbone 연결과 제한된 운영 데이터 전송 시스템을 수시간 끊고, 전용 EU 인터넷 경로와 Direct Connect를 이용해 서비스를 유지하는 시험을 예고했다.

2026-10-02 브리핑의 [KT클라우드 AIDC 운영 플랫폼 보도](https://www.bloter.net/news/articleView.html?idxno=674805)와 [네이버클라우드 AI Factory 풀스택 보도](https://www.bloter.net/news/articleView.html?idxno=674818)(모두 2026-10-01)는 GPU 보유량만큼 운영 소프트웨어, Cloud Platform, Network·Storage·Security를 함께 보는 관점이 중요하다고 설명했다. 이 문제도 여러 환경의 상태와 의존성을 한 모델에서 확인하는 기존 질문과 겹쳐 새 랩을 만들지 않았다.

제품 없이도 핵심 개념부터 확인해 보고 싶었다. 그래서 질문을 **“읽기 전용 토폴로지로 정상 경로, 단일 장애, 금지 흐름, 외부 의존성 제거 뒤의 대체 경로와 AIDC 운영 사각지대를 변경 전에 판정할 수 있을까?”**로 넓혔다. 아래 JSON 모델과 시나리오는 원문 구성을 그대로 복제한 것이 아니라 내가 만든 합성 환경이다.

## 내가 만든 축소 모델

- 상태: **로컬 검증**
- 환경: Python 3 표준 라이브러리, 합성 JSON 토폴로지
- 기존 입력: 2 Spine·2 Leaf, 애플리케이션·게스트·관리 워크로드, 거부 흐름 1개
- 추가 입력: Global Backbone, 전용 EU Internet, Direct Connect, 제한된 운영 데이터 전송 시스템, 합성 AIDC 통합 Control Plane과 Public·Private·On-Prem API 엔드포인트
- 판정: 모든 단순 경로 계산, 노드 장애 반영, 정책 거부 후 유효 경로 산출

```text
client / guest -- leaf1 -- spine1 -- leaf2 -- app / admin
                        \ spine2 /

external-client -- global-backbone -- sovereign-edge -- sovereign-service
               \-- eu-internet -----/                    /
private-client -------- direct-connect ------------------/

AIDC operator -- unified-control-plane -- public-cloud-api
                                      |-- private-cloud-api
                                      `-- onprem-api
```

## 실행

```powershell
cd F:\main\labs\10-network-digital-twin
python .\validate.py --model .\model.json --evidence .\evidence\2026-10-02.json
```

## 직접 계산한 결과

[2026-10-02 실행 증적](evidence/2026-10-02.json):

| 시나리오 | 의도 | 관측 | 판정 |
|---|---|---|---|
| 정상 | `client → app` 경로 2개 이상 | Spine별 경로 2개 | 통과 |
| 정상 | `guest → admin` 차단 | 토폴로지 경로 2개, 정책 적용 후 유효 경로 0개 | 통과 |
| spine1 중단 | `client → app` 도달 가능 | spine2 경로 1개 | 통과 |
| 두 Spine 중단 | `client → app` 도달 불가 | 경로 0개 | 통과 |
| Sovereign 정상 | 외부 Client 경로 2개 이상, Private Client 경로 유지 | Backbone·EU Internet 2개, Direct Connect 1개 | 통과 |
| Global 시스템 분리 | Backbone과 운영 전송 노드가 없어도 두 Client 도달 가능 | EU Internet 1개, Direct Connect 1개 | 통과 |
| AIDC Control Plane 정상 | 운영자에서 Public·Private·On-Prem API 모두 도달 | 각 엔드포인트 경로 1개 | 통과 |
| Private Cloud API 중단 | Public·On-Prem은 유지하고 Private만 관측 불가 | Public 1개·Private 0개·On-Prem 1개 | 통과 |

증적에는 입력 모델 SHA-256, 비활성 노드, 계산한 경로, 정책 적용 전후 경로 수가 포함된다. 2026-09-26 첫 모델과 [2026-09-30 확장 모델 증적](evidence/2026-09-30.json)도 지우지 않았다.

## 계산하면서 보인 한계

- 실제 장비, IP Fabric 제품, AWS European Sovereign Cloud, Direct Connect, KT클라우드나 네이버클라우드 제품을 사용하지 않았다.
- AWS가 예고한 2026-10-24 시험 결과를 미리 성공으로 쓴 것이 아니다. 이번 결과는 발표에 나온 의존성 구조를 내가 단순화해 계산한 값이다.
- JSON 모델은 운영망에서 자동 수집한 상태가 아니므로 입력이 틀리면 결과도 틀릴 수 있다.
- 라우팅 프로토콜 수렴, BGP 경로 선택, ACL 우선순위, NAT, 포트·프로토콜, 지연·손실은 계산하지 않는다.
- 따라서 결과는 **합성 모델의 로컬 검증**이며 운영망의 실제 도달성이나 주권 요건 충족 증명이 아니다.

## 다음에 이어서 할 일

1. [01 BGP/ECMP](../bgp-ecmp/README.md)의 FRR running-config와 경로 출력을 읽기 전용 수집기로 변환한다.
2. 변경 전후 스냅샷을 비교해 의도 위반과 영향받는 애플리케이션을 표시한다.
3. 포트·프로토콜, ACL, BGP 수렴 시간과 증적 서명을 추가한다.
4. 실제 Public·Private·On-Prem API에서 읽기 전용 인벤토리를 수집해 합성 Control Plane 모델과 대조한다.
