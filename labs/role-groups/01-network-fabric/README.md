# Network Fabric & Traffic Engineering

**Primary role group** `01-network-fabric` · **이관 자료는 런타임 재검증 전**

이 역할군은 하나의 *운영 책임 경계*와 **재현 가능한 통합 검증 흐름**을 제공해. 원본 개별 랩은 유일한 소스의 진실이며 이 인덱스는 코드 복제/성공 상태 승격이 아님.

## 운영 목적
L2/L3 underlay·overlay·경로·로드밸런싱과 장애 우회 경로의 재현성

## 단일 실습 흐름
BGP/ECMP(01) → EVPN/VXLAN(02) → Digital Twin(10) → AI/DC 병목(08,12) → HA Proxy/Service Topology(09,43) → EVE-NG 현황 비교(33)

## 소속 랩

| ID | 랩 (canonical) | 현재 출처 기반 상태 |
|---|---|---|
| 01 | [01-bgp-ecmp](../../01-bgp-ecmp/README.md) | 기존 로컬 검증 기록 |
| 02 | [02-evpn-vxlan](../../02-evpn-vxlan/README.md) | 기존 로컬 검증 기록 |
| 08 | [08-ai-dc-network](../../08-ai-dc-network/README.md) | 기존 로컬 검증 기록 |
| 09 | [09-load-balancer-ha](../../09-load-balancer-ha/README.md) | 기존 로컬 검증 기록 |
| 10 | [10-network-digital-twin](../../10-network-digital-twin/README.md) | 기존 로컬 검증 기록 |
| 12 | [12-ai-multiregion-data-path](../../12-ai-multiregion-data-path/README.md) | 기존 로컬 검증 기록 |
| 33 | [33-eve-network-assurance](../../33-eve-network-assurance/README.md) | 이관·재검증 대기 |
| 43 | [43-dandelion-service-topology](../../43-dandelion-service-topology/README.md) | 이관·재검증 대기 |

## 통합 대상, 중복 기능 정리
- 01+02+10: 경로/세그먼트 기본 구조와 변경 전 모델을 통합 검증
- 09+43: HAProxy 백엔드·Web/DB 장애 경계를 공통 서비스 토폴로지로 정리

## 역할군 공통 인터페이스

- **Input:** synthetic topology, device configs, VLAN/VNI, BGP neighbors, link/host failure toggles
- **Output:** route/adversity matrix, reachability JSON, overlay FDB, failover timeline
- **Mandatory gate:** 정상, 경로 상실, 스파인 장애, 미허용 세그먼트 차단, 복구 후 수렴

개별 랩에서 입력·출력 형식을 먼저 고정한 뒤 기능을 연결해. 기존 성공/실패 증적은 해당 랩에 유지하고, 통합 흐름의 결과는 **새로운 증적**을 따로 남겨야 해. 읽기 전용 관측과 변경·배포·삭제 코드는 같은 권한으로 실행하지 않음.

## 다음 조합 단계
1. 모든 랩의 의존성/하드코딩 경로를 해소하고 합성 데이터를 표준화한다.
2. 최소 단위 정상/거부/장애/복구 검증 후 통합 대상으로 승격한다.
3. 공통 인터페이스에 맞춰 각 랩을 조합하고 전체 흐름·회귀·롤백을 재검증한다.
4. 기존 `labs/NN-...` 경로는 링크/증적 보존을 위해 유지하며, 완성된 통합 코드만 향후 역할군 하위에 작성한다.

[전체 역할군 목록](../README.md) · [인터페이스 규격](../../../docs/lab-interface-contract.md)
