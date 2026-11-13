# BGP EVPN / VXLAN L2VNI Lab

## 이걸 해본 이유

[Cisco의 AI 네트워크 글(2026-09-21)](https://blogs.cisco.com/news/the-ai-era-demands-more-than-speed-building-secure-intelligent-networks-from-silicon-to-optics)을 보고 ECMP 다음 단계로 세그먼트 분리를 확인해 보기로 했다. **같은 VNI끼리는 통신하고 다른 VNI끼리는 실제로 분리되는가?**를 FRR과 Linux VXLAN으로 시험했다. 이 토폴로지는 기사 예제가 아니라 내가 만든 축소 환경이다.

2026-09-22 첫 실행 뒤 2026-09-29에 WSL2의 FRR 컨테이너 두 대로 L2VNI를 다시 확인했다. 2-Spine Underlay와 L3VNI는 이번 실행에 넣지 않았다.

[삼성·SKT·하나금융 Private 5G 발표(2026-09-28)](https://news.samsung.com/global/samsung-sk-telecom-and-hana-financial-group-buildkoreas-first-private-5g-smart-office-in-the-financial-sector/)에서는 하나의 물리 인프라를 계열사별 Network Slice로 나눠 독립 운영 환경과 보안 정책을 적용했다고 설명한다. 5G SA Core와 Network Slicing을 구현한 것은 아니지만, **공유 인프라 위에서 논리 세그먼트가 섞이지 않는가**라는 기존 질문과 겹쳐 새 랩을 만들지 않고 이 실습에 연결했다.

## 확인하려던 것

같은 물리 Underlay 위에서 두 논리 세그먼트를 운반할 때, 같은 VNI의 원격 Host는 통신하고 서로 다른 VNI의 Host는 같은 IP 대역을 사용해도 L2로 연결되지 않아야 한다.

## 토폴로지

```text
Host1 (.11) -- VNI 100 -- Leaf1 ==== Underlay ==== Leaf2 -- VNI 100 -- Host2 (.12)
Host3 (.13) -- VNI 200 -- Leaf1 ==== 10.202.0.0/30 ==== Leaf2 -- VNI 200 -- Host4 (.14)
                                  VTEP .1              VTEP .2
```

- Leaf1/Leaf2: AS 65200의 직접 iBGP EVPN 이웃. Underlay는 10.202.0.1/30 ↔ 10.202.0.2/30 veth 링크이다.
- VTEP: 10.255.1.1/32 ↔ 10.255.1.2/32. BGP IPv4 Unicast가 VTEP /32를 교환한다.
- VNI 100·200: 각각 Linux bridge와 VXLAN 인터페이스에 매핑한다. FRR의 `advertise-all-vni`가 EVPN 제어면을 활성화한다.
- 네 Host 모두 실습용 192.0.2.0/24 대역을 사용한다. VNI 100과 200이 분리돼 있는지 보기 위한 의도적 구성이다.

## 구성하고 실행한 방법

WSL2 Ubuntu에 Docker Engine, Compose, 비대화형 `sudo ip link`가 필요한다.

```bash
bash labs/role-groups/01-network-fabric/experiments/evpn-vxlan/run-lab.sh
```

스크립트는 Docker `network_mode: none`에서 시작한 뒤 직접 veth 링크를 연결한다. Host 연결과 VXLAN 터널은 컨테이너 네임스페이스 안에만 존재하며, 공개 포트는 없다. 끝나면 이 랩의 컨테이너를 제거한다.

[Compose 설정](compose.yaml), [Leaf1 FRR 설정](configs/leaf1/frr.conf), [Leaf2 FRR 설정](configs/leaf2/frr.conf), [실행 스크립트](run-lab.sh).

## 직접 돌려본 결과

[2026-09-29 재실행 출력](evidence/2026-09-29.txt):

| 확인 항목 | 관측 결과 |
|---|---|
| Leaf1 BGP EVPN 이웃 | Leaf2와 Established, EVPN 프리픽스 3개 수신 |
| VNI 100/200 | 둘 다 L2 VNI로 감지, 각 VNI의 Remote VTEP 1개 |
| 원격 FDB | VNI 100의 원격 MAC이 10.255.1.2로 설치 |
| Host1 → Host2 (VNI 100) | ping 3/3 |
| Host3 → Host4 (VNI 200) | ping 3/3 |
| Host1 → Host3 (다른 VNI) | ping 0/2, 연결 안 됨 |

Host1에서 Host3으로는 같은 IP 프리픽스의 주소를 ARP로 찾지만, 서로 다른 Bridge/VNI에 있어 응답을 받지 못했다. 두 양성 테스트와 EVPN 이웃·VNI·FDB 출력을 함께 확인해 단순 단절이 아니라 의도한 세그먼트 분리임을 확인했다.

## 남은 점

- 두 Leaf를 직접 연결한 소규모 Underlay이다. 멀티 홉 Spine-Leaf Fabric, Route Reflector, L3VNI, Anycast Gateway, MTU·성능 시험은 아직 하지 않았다.
- 2026-09-22 첫 출력에는 `vtysh.conf` 누락 경고가 있었다. 파일과 소유권을 고친 뒤 2026-09-29 재실행에서는 해당 경고 없이 같은 통신·격리 결과를 확인했다.
- 이 결과는 합성 컨테이너 랩의 로컬 검증이며, 금융 네트워크 또는 실제 데이터센터의 배포 증거가 아닙니다.

## 참고한 문서

- [FRR EVPN 개념, VXLAN dataplane, advertise-all-vni](https://docs.frrouting.org/en/latest/evpn.html)
- [FRR 10.7.0 릴리스](https://github.com/FRRouting/frr/releases/tag/frr-10.7.0)
