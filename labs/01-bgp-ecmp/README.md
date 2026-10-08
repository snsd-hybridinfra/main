# BGP ECMP Spine-Leaf Lab

## 이걸 해본 이유

[Cisco의 AI 네트워크 글(2026-09-21)](https://blogs.cisco.com/news/the-ai-era-demands-more-than-speed-building-secure-intelligent-networks-from-silicon-to-optics)을 읽다가 복원력이라는 말을 실제 경로로 확인해 보고 싶었다. 내가 잡은 질문은 단순했다. **Spine 하나가 멈춰도 Leaf 사이 통신이 계속될까?** 기사에 나온 상용망을 흉내 내기보다 FRR로 가장 작은 BGP/ECMP 토폴로지를 직접 만들었다.

2026-10-07 [KT클라우드 청라 AI 데이터센터 보도](https://www.yna.co.kr/view/AKR20261007049600017)는 기존 가산·목동 데이터센터와의 연계 및 거점 간 연속성을 언급했다. 이 내용은 새 랩으로 만들지 않고 기존 BGP/ECMP 장애 전환 질문에 DCI 관점을 연결했다. 기사 속 KT클라우드 망이나 DCI를 재현한 것은 아니다.

2026-09-22 첫 실행 뒤 2026-09-29에 WSL2 Ubuntu와 FRR 컨테이너로 다시 실행했다. 경로와 ping은 확인했지만 EVE-NG나 물리 장비에서는 아직 돌리지 않았다.

## 확인하려던 것

두 Spine 경로를 가진 L3 Fabric에서 한 Spine이 멈춰도 Leaf 간 통신이 유지되는지 확인한다. BGP가 같은 목적지 프리픽스에 두 개의 유효한 다음 홉을 설치하는지, 장애 때 하나만 남는지, 복구 뒤 다시 둘이 되는지를 Linux 라우팅 테이블과 Host 통신으로 검증한다.

## 토폴로지

```text
        Spine1 (AS 65000)      Spine2 (AS 65000)
          /          \            /          \
         /            \          /            \
Leaf1 (AS 65101)     Leaf2 (AS 65102)
      |                      |
 Host1 10.201.101.3    Host2 10.201.102.3
```

| 링크 | Spine 주소 | Leaf 주소 |
|---|---|---|
| Spine1–Leaf1 | 10.201.11.2/29 | 10.201.11.3/29 |
| Spine1–Leaf2 | 10.201.12.2/29 | 10.201.12.3/29 |
| Spine2–Leaf1 | 10.201.21.2/29 | 10.201.21.3/29 |
| Spine2–Leaf2 | 10.201.22.2/29 | 10.201.22.3/29 |

Leaf1은 10.201.101.0/29, Leaf2는 10.201.102.0/29를 광고한다. 두 Spine은 같은 AS를 사용하고, Leaf의 `maximum-paths 2`가 동일한 경로의 ECMP 설치를 허용한다.

## 구성하고 실행한 방법

- WSL2 Ubuntu, Docker Engine 및 Compose
- [FRRouting 10.7.0](https://github.com/FRRouting/frr/releases/tag/frr-10.7.0) 공식 이미지 다이제스트 고정
- BusyBox 1.37.0 이미지 다이제스트 고정
- Docker `network_mode: none`과 WSL의 직접 veth 링크. 외부 네트워크 연결이나 공개 포트 없음.
- WSL 사용자에게 비대화형 `sudo ip link` 권한 필요. FRR 이미지의 daemon에는 `NET_ADMIN`, `NET_RAW`, `SYS_ADMIN` capability가 필요했다.

WSL에서 실행:

```bash
bash /mnt/f/main/labs/01-bgp-ecmp/run-lab.sh
```

스크립트는 라우터·호스트를 띄운 뒤 veth 6개를 연결하고, 정상 → Spine1 중단 → 복구를 검사한다. 종료 시 이 랩의 컨테이너만 제거한다. 설정은 [compose.yaml](compose.yaml), [FRR 설정](configs/leaf1/frr.conf), [실행 스크립트](run-lab.sh)에 있다.

## 직접 돌려본 결과

[2026-09-29 재실행 출력](evidence/2026-09-29.txt)에서 확인한 값:

| 단계 | Leaf1의 10.201.102.0/29 경로 | Host1 → Host2 |
|---|---|---|
| 정상 | Spine1 10.201.11.2 + Spine2 10.201.21.2 | ping 3/3 |
| Spine1 중단 | Spine2 10.201.21.2만 남음 | ping 3/3 |
| Spine1 복구 | 두 다음 홉 재설치 | ping 3/3 |

정상 상태의 Leaf1 BGP 이웃 2개가 모두 Established 상태였고 각 이웃에서 프리픽스 1개를 받았다. traceroute는 Leaf1 → Spine1 → 응답 없는 홉 → Host2를 보여줬다. 홉 하나의 `*`는 ICMP 응답을 받지 못했다는 뜻이며, 종단 간 ping과 라우팅 테이블을 통신·경로 검증의 주 근거로 사용했다.

## 하면서 확인한 한계

- FRR CLI가 vtysh.conf 누락 및 초기 설정 처리 경고를 출력했다. BGP 이웃·커널 ECMP 경로·종단 간 통신은 별도로 확인했으며, 경고 원인은 후속 정리 대상이다.
- 이번 실습은 WSL2 컨테이너의 합성 주소와 FRR로 검증했다. EVE-NG의 특정 Cisco OS 동작이나 실제 400/800G Fabric 성능을 입증하지 않다.
- 장애 중 애플리케이션 세션이 무손실로 유지되는지, 수렴 시간이 몇 ms인지 측정하지 않았다. ping 3/3은 경로가 안정된 후의 확인이다.
- 다음 실습에서는 EVPN/VXLAN의 Underlay·Overlay 분리와 세그먼트 격리를 검증한다.

## 참고한 문서

- [FRR BGP multipath 및 maximum-paths 설명](https://docs.frrouting.org/en/latest/bgp.html)
- [FRR 10.7.0 릴리스](https://github.com/FRRouting/frr/releases/tag/frr-10.7.0)
