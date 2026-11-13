# 08 AI DC Network: 공유 병목과 지연

## 이걸 해본 이유

[Cisco의 AI 네트워크 글(2026-09-21)](https://blogs.cisco.com/news/the-ai-era-demands-more-than-speed-building-secure-intelligent-networks-from-silicon-to-optics)을 읽고 “대역폭이 꽉 찼을 때 지연은 얼마나 달라질까?”부터 숫자로 확인해 보기로 했다. GPU나 RoCE 장비 대신 20 Mbit/s로 제한한 가상 링크에서 TCP 흐름 수와 ping 지연을 비교했다.

격리된 Linux 네트워크 네임스페이스에서 직접 측정했다. AI 학습 트래픽이나 GPU, RDMA/RoCE, ECN, PFC 장비를 사용한 결과는 아니다.

## 예상한 변화

여러 흐름이 제한된 링크를 함께 쓸 때 총 처리량과 지연은 어떻게 바뀌는가? 20 Mbit/s 병목을 만들면 1개·2개 TCP 흐름의 총 수신 처리량은 병목 근처로 제한되고, 동시 부하에서 큐 지연이 늘어날 것으로 예상했다.

## 병목을 만든 방법

[`run-lab.sh`](run-lab.sh)는 두 개의 Linux 네임스페이스를 veth로 연결한다. 외부 네트워크는 연결하지 않는다. `iperf3` 서버와 클라이언트를 사용해 제한 없는 단일 흐름을 3초 측정한 뒤, 클라이언트 송신 인터페이스에 `tc tbf rate 20mbit burst 32kb latency 100ms`를 설정한다. 제한된 단일 흐름을 5초, 2개 병렬 흐름을 6초 측정하고 idle/부하 중 ping 평균값을 비교한다. 종료 시 서버·네임스페이스·임시 출력을 삭제한다.

WSL2 Ubuntu 또는 Linux에서 `ip`, `tc`, `iperf3`, `ping`, Python 3과 `sudo`가 필요하다.

```bash
bash labs/role-groups/01-network-fabric/experiments/ai-dc-network/run-lab.sh
```

## 직접 측정한 결과

[2026-09-22 측정 JSON](evidence/2026-09-22.json):

| 지표 | 이 실행의 값 |
|---|---:|
| 제한 없는 가상 링크 단일 TCP | 40,206.87 Mbit/s |
| 20 Mbit/s 제한, 단일 TCP | 19.07 Mbit/s |
| 같은 제한, 2개 TCP 총합 | 19.06 Mbit/s |
| 2개 흐름 개별 수신 | 13.51 / 5.54 Mbit/s |
| idle ping 평균 | 0.035 ms |
| 부하 중 ping 평균 | 69.16 ms |
| TBF 큐 드롭 | 5 패킷 |

제한 없는 속도는 WSL 가상 링크 수치이며 실제 NIC 용량이 아니다. 2개 흐름의 단기 분배는 공정성 보증이 아니다. 이 한 번의 실험에서는 총 처리량이 대략 병목에서 유지되는 동시에 ping 지연이 커졌다. 병목 큐의 설정과 TCP 경쟁이 결과에 영향을 준다.

## 측정 뒤에 생긴 다음 질문

AI 데이터센터 네트워크를 설계할 때는 **총 대역폭뿐 아니라 혼잡 시 지연, 드롭, 흐름 간 분배**도 측정해야 한다. RoCE 환경에서는 ECN과 PFC 같은 별도 혼잡·흐름 제어 기능을 살펴봐야 한다. 다음 실습은 해당 기능을 지원하는 NIC/스위치와 실제 학습 통신 패턴에서 ECN 마크, PFC pause, 포트 큐, 지연 분포, 워크로드 단계 시간을 수집해야 한다. 이 실습의 TCP/TBF 결과로 그 기능의 성능을 추정하지 않는다.

## 참고 자료와 다음 연결

- [iperf3 공식 문서](https://software.es.net/iperf/invoking.html): 병렬 흐름과 JSON 출력.
- [Linux tc-tbf 매뉴얼](https://man7.org/linux/man-pages/man8/tc-tbf.8.html): 토큰 버킷 속도·버스트·큐 지연.
- [NVIDIA RoCE QoS 문서](https://docs.nvidia.com/networking-ethernet-software/cumulus-linux-59/Layer-1-and-Switch-Ports/Quality-of-Service/): ECN·PFC 고려 사항.
- 개인 프로젝트의 네트워크 성능 검증 항목을 정할 때 사용할 기초 실험이다. 서브 프로젝트의 AI 데이터센터망 측정값은 아니다.
