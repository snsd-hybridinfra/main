#!/usr/bin/env bash
set -euo pipefail

client_ns="lab8c-$$"
server_ns="lab8s-$$"
client_if="v8c$$"
server_if="v8s$$"
tmp=$(mktemp -d /tmp/lab08-network-XXXXXXXX)
cleanup() {
  if [ -f "$tmp/server.pid" ]; then sudo kill "$(sudo cat "$tmp/server.pid")" >/dev/null 2>&1 || true; fi
  sudo ip netns del "$client_ns" >/dev/null 2>&1 || true
  sudo ip netns del "$server_ns" >/dev/null 2>&1 || true
  case "$tmp" in /tmp/lab08-network-*) rm -rf -- "$tmp" ;; esac
}
trap cleanup EXIT

sudo ip netns add "$client_ns"
sudo ip netns add "$server_ns"
sudo ip link add "$client_if" type veth peer name "$server_if"
sudo ip link set "$client_if" netns "$client_ns"
sudo ip link set "$server_if" netns "$server_ns"
sudo ip netns exec "$client_ns" ip addr add 10.88.0.1/30 dev "$client_if"
sudo ip netns exec "$server_ns" ip addr add 10.88.0.2/30 dev "$server_if"
sudo ip netns exec "$client_ns" ip link set lo up
sudo ip netns exec "$server_ns" ip link set lo up
sudo ip netns exec "$client_ns" ip link set "$client_if" up
sudo ip netns exec "$server_ns" ip link set "$server_if" up
sudo ip netns exec "$server_ns" iperf3 -s -D -I "$tmp/server.pid" -p 5300
sleep 0.5

sudo ip netns exec "$client_ns" iperf3 -c 10.88.0.2 -p 5300 -t 3 -J > "$tmp/unshaped.json"
sudo ip netns exec "$client_ns" tc qdisc add dev "$client_if" root tbf rate 20mbit burst 32kb latency 100ms
sudo ip netns exec "$client_ns" ping -c 10 -i 0.1 10.88.0.2 > "$tmp/ping-idle.txt"
sudo ip netns exec "$client_ns" iperf3 -c 10.88.0.2 -p 5300 -t 5 -J > "$tmp/single.json"
sudo ip netns exec "$client_ns" iperf3 -c 10.88.0.2 -p 5300 -t 6 -P 2 -J > "$tmp/parallel.json" &
load_pid=$!
sleep 1
sudo ip netns exec "$client_ns" ping -c 20 -i 0.15 10.88.0.2 > "$tmp/ping-load.txt"
wait "$load_pid"
sudo ip netns exec "$client_ns" tc -s qdisc show dev "$client_if" > "$tmp/qdisc.txt"

python3 - "$tmp" <<'PY'
import json
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1])
def get_json(name):
    return json.loads((root / name).read_text())
def mbps(data):
    return round(data["end"]["sum_received"]["bits_per_second"] / 1e6, 2)
def ping_avg(name):
    text = (root / name).read_text()
    match = re.search(r"(?:rtt|round-trip) min/avg/max/(?:mdev|stddev) = [\d.]+/([\d.]+)/", text)
    if not match:
        raise RuntimeError("ping statistics missing")
    return float(match.group(1))
unshaped = get_json("unshaped.json")
single = get_json("single.json")
parallel = get_json("parallel.json")
flows = [round(s["receiver"]["bits_per_second"] / 1e6, 2)
         for s in parallel["end"]["streams"]]
qdisc = (root / "qdisc.txt").read_text()
drop_match = re.search(r"dropped (\d+)", qdisc)
result = {
    "status": "pass" if 10 <= mbps(single) <= 25 and 10 <= mbps(parallel) <= 25 else "unexpected",
    "topology": "two isolated network namespaces, one veth pair",
    "tbf_limit_mbps": 20,
    "unshaped_single_mbps": mbps(unshaped),
    "shaped_single_mbps": mbps(single),
    "shaped_two_flow_total_mbps": mbps(parallel),
    "two_flow_receiver_mbps": flows,
    "idle_ping_avg_ms": ping_avg("ping-idle.txt"),
    "loaded_ping_avg_ms": ping_avg("ping-load.txt"),
    "tbf_dropped_packets": int(drop_match.group(1)) if drop_match else None,
}
print(json.dumps(result, ensure_ascii=False, indent=2))
if result["status"] != "pass":
    raise SystemExit(1)
PY
