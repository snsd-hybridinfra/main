#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p evidence
exec > >(sed -u 's/[[:space:]]*$//' | tee evidence/2026-09-29.txt) 2>&1
cleanup() {
  docker compose down --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "BGP/ECMP lab: FRR 10.7.0, Docker network_mode=none, direct veth links"
docker compose up --build -d >/dev/null 2>&1

pid() {
  docker inspect -f '{{.State.Pid}}' "$(docker compose ps -q "$1")"
}

link_no=0
link() {
  local left="$1" left_if="$2" left_ip="$3" right="$4" right_if="$5" right_ip="$6"
  local a="labv"$link_no"a" b="labv"$link_no"b"
  link_no=$((link_no + 1))
  sudo -n ip link add "$a" type veth peer name "$b"
  sudo -n ip link set "$a" netns "$(pid "$left")"
  sudo -n ip link set "$b" netns "$(pid "$right")"
  docker compose exec -T "$left" ip link set "$a" name "$left_if"
  docker compose exec -T "$left" ip addr add "$left_ip" dev "$left_if"
  docker compose exec -T "$left" ip link set "$left_if" up
  docker compose exec -T "$right" ip link set "$b" name "$right_if"
  docker compose exec -T "$right" ip addr add "$right_ip" dev "$right_if"
  docker compose exec -T "$right" ip link set "$right_if" up
}

link spine1 l1 10.201.11.2/29 leaf1 s1 10.201.11.3/29
link spine1 l2 10.201.12.2/29 leaf2 s1 10.201.12.3/29
link spine2 l1 10.201.21.2/29 leaf1 s2 10.201.21.3/29
link spine2 l2 10.201.22.2/29 leaf2 s2 10.201.22.3/29
link leaf1 h1 10.201.101.2/29 host1 eth0 10.201.101.3/29
link leaf2 h2 10.201.102.2/29 host2 eth0 10.201.102.3/29
docker compose exec -T host1 ip route add default via 10.201.101.2
docker compose exec -T host2 ip route add default via 10.201.102.2

wait_paths() {
  local expected="$1" count
  for attempt in $(seq 1 45); do
    count=$(docker compose exec -T leaf1 ip route show 10.201.102.0/29 | grep -c 'nexthop via' || true)
    if [ "$expected" -eq 1 ]; then
      if docker compose exec -T leaf1 ip route show 10.201.102.0/29 | grep -q 'via 10.201.21.2'; then return 0; fi
    elif [ "$count" -eq "$expected" ]; then
      return 0
    fi
    sleep 1
  done
  echo "Expected $expected path(s), got:"
  docker compose exec -T leaf1 ip route show 10.201.102.0/29
  return 1
}

wait_paths 2
echo "=== Normal: BGP sessions ==="
docker compose exec -T leaf1 vtysh -c "show ip bgp summary"
echo "=== Normal: ECMP route ==="
docker compose exec -T leaf1 ip route show 10.201.102.0/29
echo "=== Normal: Host1 -> Host2 ==="
docker compose exec -T host1 ping -c 3 -W 2 10.201.102.3
docker compose exec -T host1 traceroute -n -m 5 -w 1 -q 1 10.201.102.3 || true

echo "=== Failure: stop Spine1 ==="
docker compose stop -t 2 spine1 >/dev/null
wait_paths 1
docker compose exec -T leaf1 ip route show 10.201.102.0/29
docker compose exec -T host1 ping -c 3 -W 2 10.201.102.3

echo "=== Recovery: restart Spine1 and restore its two links ==="
docker compose up -d spine1 >/dev/null
link spine1 l1 10.201.11.2/29 leaf1 s1 10.201.11.3/29
link spine1 l2 10.201.12.2/29 leaf2 s1 10.201.12.3/29
wait_paths 2
docker compose exec -T leaf1 ip route show 10.201.102.0/29
docker compose exec -T host1 ping -c 3 -W 2 10.201.102.3
echo "PASS: normal ECMP, Spine1 failure survival, ECMP recovery"
