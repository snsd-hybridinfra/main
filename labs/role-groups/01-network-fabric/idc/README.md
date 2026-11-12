# IDC Network Fabric

[토폴로지와 주소표](architecture.md) · [단계별 학습·검증 체크리스트](roadmap.md) · [측정 결과](../../07-recovery-dr/idc/validation.md)

## FRRouting 환경

전용 Debian 13 Linux VM에서 실행합니다. 실행기는 6개의 `idc-*` 네임스페이스와 FRR pathspace를 생성하며 BGP는 네임스페이스 안에서 동작합니다. FRR 서비스와 인터페이스는 기본 네임스페이스와 분리됩니다. 사용한 FRR은 Debian 패키지의 10.3 계열입니다. Linux VRF, VXLAN, 802.1Q VLAN, veth 기능이 필요합니다. [FRRouting EVPN 가이드](https://docs.frrouting.org/en/stable-10.3/evpn.html)

```sh
sudo apt-get update
sudo apt-get install -y frr iproute2 iputils-ping curl python3
mkdir -p .runtime/idc
python3 tools/idc.py render --check
sudo python3 tools/idc.py fabric up
sudo python3 tools/idc.py verify --wait 60 --out .runtime/idc/baseline.json
```

기준선은 장비별 IPv4·EVPN 이웃 2개씩, 양쪽 Leaf에서 원격 VTEP까지 커널 next hop 2개, VLAN 10의 IMET과 원격 MAC 학습, TENANT의 Type 5 프리픽스 설치와 기본 라우팅 테이블 격리입니다. Host1에서 1500바이트 IPv4 L2 패킷과 L3 ICMP, 두 경로의 HTTP를 확인합니다.

VM의 셸에서 VTY 확인 명령을 다음과 같이 지정합니다.

```sh
idc_vty() {
  sudo vtysh --vty_socket "/run/frr/idc-$1" --config_dir "/run/idc-resilience/$1" -c "$2"
}
```

| 확인 대상 | 예시 명령 |
|---|---|
| 언더레이·오버레이 BGP | `idc_vty leaf1 'show bgp ipv4 unicast summary'` · `idc_vty leaf1 'show bgp l2vpn evpn summary'` |
| 원격 VTEP FIB | `sudo ip -n idc-leaf1 -4 route show exact 192.0.2.12/32` · `sudo ip -n idc-leaf1 nexthop show` |
| Type 2/3 데이터 경로 | `sudo ip netns exec idc-leaf1 bridge fdb show dev vx1010` |
| L3 VNI와 Type 5 | `idc_vty leaf1 'show evpn vni 50000'` · `sudo ip -n idc-leaf1 -4 route show vrf TENANT` |

`topology.json`이 설정과 NetBox 데이터의 원본입니다. 값을 수정했다면 `python3 tools/idc.py render`로 설정을 갱신하고, `python3 tools/idc.py inventory --out labs/role-groups/01-network-fabric/idc/netbox-inventory.json`으로 원장 계획을 갱신합니다. 모든 단계 종료 후 `sudo python3 tools/idc.py fabric down`으로 랩 네임스페이스를 정리합니다.

## EVE-NG와 Arista EOS

[EOS 후보 설정](configs/eos/)은 vEOS-lab 4.30 계열을 대상으로 작성했습니다. 실습 결과는 FRRouting 기준입니다. vEOS-lab과 Aboot는 다운로드 권한과 사용 조건을 확인해 공식 배포 경로에서 확보합니다. EVE-NG 공식 가이드의 예시 버전은 4.32.5와 4.34.0F입니다. 4.30 설치에 사용할 이미지·Aboot 조합과 가상 하드웨어 요구사항을 실습 전에 확인합니다. 공식 배포판에서 설치할 수 있는 오픈소스 FRRouting으로 동일 토폴로지를 실습할 수 있습니다. [Arista 다운로드 안내](https://www.arista.com/en/support/customer-support) · [Arista EULA](https://www.arista.com/assets/data/pdf/software-agreement/EndUserLicenseAgreement.pdf) · [EVE-NG vEOS 가이드](https://www.eve-ng.net/index.php/documentation/howtos/howto-add-arista-veos/) · [FRRouting 프로젝트](https://frrouting.org/)

1. EVE-NG에서 vEOS-lab 4개와 VLAN 태깅이 가능한 Linux Host 2개를 배치합니다. Linux `eth1`·`eth2`·`eth3`와 EOS의 동일 번호 `Ethernet`을 [토폴로지](architecture.md)대로 연결합니다.
2. 콘솔에서 각 노드에 해당하는 `*.cfg`를 적용합니다. 멀티 에이전트 모드의 적용 상태를 확인하고 이미지에서 요구하는 경우 재부팅합니다. `show version`과 명령 수용 결과를 기록합니다.
3. 두 Host에서 각 `host*.sh`를 전용 트렁크 NIC 이름으로 실행합니다. 예를 들어 Host1에서 `sudo sh host1.sh eth1`을 실행합니다. Host2에서 `service.py`를 옮겨 `python3 service.py 8080`으로 띄웁니다.
4. `show ip bgp summary`, `show bgp evpn summary`, `show ip route 192.0.2.12/32`와 `show interfaces Vxlan1`을 확인합니다. `show bgp evpn route-type imet`, `show bgp evpn route-type mac-ip`, `show bgp evpn route-type ip-prefix ipv4`, `show ip route vrf TENANT`을 대조합니다.
5. Host1에서 `ping -M do -s 1472 198.51.100.12`와 `curl http://198.51.100.135:8080/healthz`를 확인합니다. U1 링크를 내리고 Leaf1의 VTEP next hop이 2개에서 1개로 줄어드는지 본 뒤, 원복하고 다시 확인합니다.

## NetBox 4.5 인벤토리

[등록 계획](netbox-inventory.json)은 장비, 물리·가상 인터페이스, 케이블, VLAN/VNI, VRF, IP 주소·프리픽스, 합성 회선과 A/Z 종단을 포함합니다. 회선은 원장 실습용이고 실제 패브릭 트래픽은 그림의 6개 링크를 이용합니다. 먼저 로컬 계획을 비교합니다.

```sh
python3 tools/idc.py inventory --out .runtime/idc/netbox-plan.json
diff -u labs/role-groups/01-network-fabric/idc/netbox-inventory.json .runtime/idc/netbox-plan.json
```

전용 NetBox 4.5 인스턴스에서 인벤토리 쓰기 권한이 있는 API 토큰을 발급합니다. Bash에서 인스턴스 주소를 지정하고 토큰을 입력합니다. 예시는 같은 VM의 루프백입니다.

```bash
export NETBOX_URL=http://127.0.0.1:8000
read -rsp 'NetBox v2 token: ' NETBOX_TOKEN
printf '\n'
export NETBOX_TOKEN
python3 tools/idc.py inventory --apply --out .runtime/idc/netbox-first.json
python3 tools/idc.py inventory --apply --out .runtime/idc/netbox-repeat.json
unset NETBOX_TOKEN
```

같은 원장에 반복 적용하면 일치하는 객체를 재사용합니다. 이미 등록된 객체의 속성이 다르면 차이를 출력하고 중단합니다. NetBox UI에서 `idc-lab` 사이트의 장비 6대, 인터페이스 24개, 케이블 6개, 회선 1개를 확인합니다. [NetBox REST API](https://netbox.readthedocs.io/en/feature/integrations/rest-api/)
