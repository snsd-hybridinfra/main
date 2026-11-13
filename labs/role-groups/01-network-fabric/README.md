# Network Fabric & Traffic Engineering

모델이 예측한 경로를 실제 패브릭의 BGP·FIB·서비스 상태와 대조합니다.

## 실행

저장소 루트에서 실행합니다.

```sh
python3 tools/run_role.py 01-network-fabric
```

Digital Twin의 경로 모델을 검증하고 같은 IDC 토폴로지에서 생성한 FRR·EOS 설정 10개를 대조합니다. NetBox 등록 계획을 JSON으로 출력합니다.

[IDC 패브릭 실행과 원장 적용](idc/README.md) · [토폴로지와 의존성](idc/architecture.md)

## 실험

| 실험 | 검증 기록 |
|---|---|
| [BGP ECMP Spine-Leaf Lab](experiments/bgp-ecmp/README.md) | 기존 로컬 검증 기록 |
| [BGP EVPN / VXLAN L2VNI Lab](experiments/evpn-vxlan/README.md) | 기존 로컬 검증 기록 |
| [AI DC Network: 공유 병목과 지연](experiments/ai-dc-network/README.md) | 기존 로컬 검증 기록 |

<details>
<summary>다른 실험 보기</summary>

| 실험 | 검증 기록 |
|---|---|
| [Edge Load Balancer HA: 관리면·사용자망·OT망 분리와 백엔드 장애 복구](experiments/load-balancer-ha/README.md) | 기존 로컬 검증 기록 |
| [Network Digital Twin: 애플리케이션 경로·AIDC Control Plane 의도 검증](experiments/network-digital-twin/README.md) | 기존 로컬 검증 기록 |
| [AI Multi-Region Data Path: Hub 원본과 Spoke 캐시](experiments/ai-multiregion-data-path/README.md) | 기존 로컬 검증 기록 |
| [EVE-NG Routing Model & Read-Only Assurance](experiments/eve-network-assurance/README.md) | 이관 자료 · 개별 재검증 전 |
| [OpenStack Service Topology & HA Boundaries](experiments/dandelion-service-topology/README.md) | 이관 자료 · 개별 재검증 전 |

</details>

[전체 랩](../README.md) · [공통 실행 기록](../evidence/2026-11-12.json)
