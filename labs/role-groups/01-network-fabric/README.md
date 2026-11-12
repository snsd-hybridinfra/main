# Network Fabric & Traffic Engineering

모델이 예측한 경로를 실제 패브릭의 BGP·FIB·서비스 상태와 대조합니다.

## 실행

저장소 루트에서 실행합니다.

```sh
python3 tools/run_role.py 01-network-fabric
```

Digital Twin의 경로 모델을 검증하고 같은 IDC 토폴로지에서 생성한 FRR·EOS 설정 10개를 대조합니다. NetBox 등록 계획을 JSON으로 출력합니다.

[IDC 패브릭 실행과 원장 적용](idc/README.md) · [토폴로지와 의존성](idc/architecture.md)

## 번호 랩

| ID | 실습과 자료 | 번호 랩의 기록 |
|---|---|---|
| 01 | [01-bgp-ecmp](../../01-bgp-ecmp/README.md) | 기존 로컬 증적 |
| 02 | [02-evpn-vxlan](../../02-evpn-vxlan/README.md) | 기존 로컬 증적 |
| 08 | [08-ai-dc-network](../../08-ai-dc-network/README.md) | 기존 로컬 증적 |
| 09 | [09-load-balancer-ha](../../09-load-balancer-ha/README.md) | 기존 로컬 증적 |
| 10 | [10-network-digital-twin](../../10-network-digital-twin/README.md) | 기존 로컬 증적 |
| 12 | [12-ai-multiregion-data-path](../../12-ai-multiregion-data-path/README.md) | 기존 로컬 증적 |
| 33 | [33-eve-network-assurance](../../33-eve-network-assurance/README.md) | 이관 참고 |
| 43 | [43-dandelion-service-topology](../../43-dandelion-service-topology/README.md) | 이관 참고 |

[역할 랩 인덱스](../README.md) · [대표 사례 검증 결과](../evidence/2026-11-12.json)
