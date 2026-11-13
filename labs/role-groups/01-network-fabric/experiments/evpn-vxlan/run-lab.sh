#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p evidence
exec > >(sed -u 's/[[:space:]]*$//' | tee evidence/2026-09-29.txt) 2>&1
cleanup() { docker compose down --remove-orphans >/dev/null 2>&1 || true; }
trap cleanup EXIT

echo "EVPN/VXLAN lab: two FRR leaves, VNI 100 and 200, direct isolated veth underlay"
docker compose up --build -d >/dev/null 2>&1
pid() { docker inspect -f '{{.State.Pid}}' "$(docker compose ps -q "$1")"; }
link_no=0
link() {
  local left="$1" left_if="$2" left_ip="$3" right="$4" right_if="$5" right_ip="$6"
  local a="evv"$link_no"a" b="evv"$link_no"b"
  link_no=$((link_no + 1))
  sudo -n ip link add "$a" type veth peer name "$b"
  sudo -n ip link set "$a" netns "$(pid "$left")"
  sudo -n ip link set "$b" netns "$(pid "$right")"
  docker compose exec -T "$left" ip link set "$a" name "$left_if"
  if [ "$left_ip" != "-" ]; then docker compose exec -T "$left" ip addr add "$left_ip" dev "$left_if"; fi
  docker compose exec -T "$left" ip link set "$left_if" up
  docker compose exec -T "$right" ip link set "$b" name "$right_if"
  if [ "$right_ip" != "-" ]; then docker compose exec -T "$right" ip addr add "$right_ip" dev "$right_if"; fi
  docker compose exec -T "$right" ip link set "$right_if" up
}
link leaf1 uplink 10.202.0.1/30 leaf2 uplink 10.202.0.2/30
link leaf1 h100 - host1 eth0 192.0.2.11/24
link leaf2 h100 - host2 eth0 192.0.2.12/24
link leaf1 h200 - host3 eth0 192.0.2.13/24
link leaf2 h200 - host4 eth0 192.0.2.14/24

configure_leaf() {
  local leaf="$1" vtep="$2"
  docker compose exec -T "$leaf" ip link set lo up
  docker compose exec -T "$leaf" ip addr add "$vtep/32" dev lo
  for vni in 100 200; do
    docker compose exec -T "$leaf" ip link add "br$vni" type bridge
    docker compose exec -T "$leaf" ip link set "br$vni" up
    docker compose exec -T "$leaf" ip link add "vx$vni" type vxlan id "$vni" local "$vtep" dev uplink dstport 4789 nolearning
    docker compose exec -T "$leaf" ip link set "vx$vni" master "br$vni"
    docker compose exec -T "$leaf" ip link set "vx$vni" type bridge_slave learning off
    docker compose exec -T "$leaf" ip link set "vx$vni" up
    docker compose exec -T "$leaf" ip link set "h$vni" master "br$vni"
    docker compose exec -T "$leaf" ip link set "h$vni" up
  done
}
configure_leaf leaf1 10.255.1.1
configure_leaf leaf2 10.255.1.2

echo "=== EVPN peering and VNI discovery ==="
for attempt in $(seq 1 40); do
  if docker compose exec -T host1 ping -c 1 -W 1 192.0.2.12 >/dev/null 2>&1; then break; fi
  sleep 1
done
docker compose exec -T leaf1 vtysh -c "show bgp l2vpn evpn summary"
docker compose exec -T leaf1 vtysh -c "show evpn vni"
docker compose exec -T leaf1 bridge fdb show dev vx100

echo "=== VNI 100: Host1 -> Host2 ==="
docker compose exec -T host1 ping -c 3 -W 2 192.0.2.12
echo "=== VNI 200: Host3 -> Host4 ==="
docker compose exec -T host3 ping -c 3 -W 2 192.0.2.14
echo "=== Isolation: Host1 must not reach Host3 across VNI 100/200 ==="
if docker compose exec -T host1 ping -c 2 -W 1 192.0.2.13; then
  echo "FAIL: VNI isolation bypass"
  exit 1
fi
echo "PASS: both VNIs connect their own hosts; cross-VNI ping is denied"
