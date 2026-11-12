"""Verify IPv4/EVPN BGP, kernel ECMP, L2/L3 VNI and service health."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time

from .model import DATA, L3_BRIDGE, L3_VNI, LEAVES, ROUTERS, SHARED, VLANS, VRF
from .model import leaf_vlans, local_prefix, peers, probe_ips
from .runtime import ERRORS, describe, ip, net, require_ready, vty

FAMILIES = {"ipv4": "ipv4 unicast", "evpn": "l2vpn evpn"}
HTTP_BODY = '{"service":"idc-lab","status":"ok"}'


def utc():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def peer_states(node, family):
    data = json.loads(vty(node, f"show bgp {FAMILIES[family]} summary json").stdout)
    found = data.get("peers")
    if found is None:
        found = next((af["peers"] for af in data.values() if isinstance(af, dict) and "peers" in af), {})
    return {neighbor: found.get(neighbor, {}).get("state", "Missing") for neighbor, _ in peers(node, family)}


def route(node, destination, scope=("table", "main")):
    return json.loads(ip(node, "-j", "-4", "route", "show", *scope, "exact", destination).stdout)


def next_hops(node, destination):
    routes = route(node, destination)
    if not routes:
        return []
    row = routes[0]
    if "nexthops" in row:
        return sorted({hop["gateway"] for hop in row["nexthops"] if "gateway" in hop})
    if "nhid" in row:
        objects = {hop["id"]: hop for hop in json.loads(ip(node, "-j", "nexthop", "show").stdout)}
        hop = objects.get(row["nhid"], {})
        members = [objects.get(member["id"], {}) for member in hop.get("group", [])] or [hop]
        return sorted({member["gateway"] for member in members if "gateway" in member})
    return [row["gateway"]] if "gateway" in row else []


def ports(node):
    return {row["ifname"]: row for row in json.loads(ip(node, "-j", "-s", "link", "show").stdout)}


def ping(path, payload=None):
    source, target = probe_ips(path)
    args = ["-M", "do", "-s", str(payload)] if payload else []
    result = net("host1", "ping", "-n", "-c", "1", "-W", "0.20", "-I", source, *args, target,
                 check=False, timeout=3, env={**os.environ, "LC_ALL": "C"})
    if result.returncode not in (0, 1) or "1 packets transmitted" not in result.stdout:
        raise RuntimeError(result.stderr.strip() or "ICMP probe failed to execute")
    return result.returncode == 0


def http(path="l3"):
    source, target = probe_ips(path)
    result = net("host1", "curl", "--noproxy", "*", "--silent", "--fail", "--interface", source,
                 "--max-time", "0.45", f"http://{target}:{DATA['service_port']}/healthz",
                 timeout=3, check=False)
    if result.returncode not in (0, 7, 22, 28, 52, 55, 56):
        raise RuntimeError(f"HTTP probe execution failed (exit {result.returncode})")
    return result.returncode == 0 and result.stdout.strip() == HTTP_BODY


def inspect_leaf(node):
    other = next(leaf for leaf in LEAVES if leaf != node)
    remote = ROUTERS[other]["loopback"]
    remote_mac = f"02:00:00:00:01:0{other[-1]}"
    fdb = json.loads(net(node, "bridge", "-j", "fdb", "show", "dev", f"vx{VLANS[SHARED]['vni']}").stdout)
    l3 = json.loads(vty(node, f"show evpn vni {L3_VNI} json").stdout)
    tenant = local_prefix(other)
    return {
        "next_hops": next_hops(node, remote + "/32"),
        "imet": any(row.get("dst") == remote and row.get("mac") == "00:00:00:00:00:00" for row in fdb),
        "remote_mac": any(row.get("dst") == remote and row.get("mac") == remote_mac for row in fdb),
        "l3vni": {key: l3.get(key) for key in ("vni", "type", "tenantVrf", "state", "l2Vnis")},
        "tenant_routes": [row for row in route(node, tenant, ("vrf", VRF))
                          if row.get("gateway") == remote and row.get("protocol") == "bgp"
                          and row.get("dev") == L3_BRIDGE],
        "underlay_isolated": not route(node, tenant),
    }


def check():
    failures = []

    def sample(name, query, *args):
        try:
            return query(*args)
        except ERRORS as error:
            failures.append(f"{name}: {describe(error)}")
            return None

    tasks = {
        **{f"{node}/{family}": (peer_states, node, family) for node in ROUTERS for family in FAMILIES},
        "l2_mtu": (ping, "l2", 1472), "l3_icmp": (ping, "l3"),
        "l2_http": (http, "l2"), "l3_http": (http, "l3"),
    }
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {name: pool.submit(sample, name, *job) for name, job in tasks.items()}
        observed = {name: job.result() for name, job in futures.items()}
    neighbors = {name: value for name, value in observed.items() if "/" in name}
    probes = {name: value for name, value in observed.items() if "/" not in name}
    failures.extend(name for name, states in neighbors.items()
                    if states is not None and any(state != "Established" for state in states.values()))
    failures.extend(name for name, healthy in probes.items() if not healthy)
    leaves = {node: sample(node, inspect_leaf, node) for node in LEAVES}
    for node, state in leaves.items():
        if state is None:
            continue
        if state["next_hops"] != sorted(addr for addr, _ in peers(node, "ipv4")):
            failures.append(f"{node}: ECMP next hops")
        for key in ("imet", "remote_mac", "tenant_routes", "underlay_isolated"):
            if not state[key]:
                failures.append(f"{node}: {key}")
        l3 = state["l3vni"]
        expected = sorted(VLANS[vlan]["vni"] for vlan in leaf_vlans(node))
        if ((l3["vni"], l3["type"], l3["tenantVrf"], l3["state"]) != (L3_VNI, "L3", VRF, "Up")
                or sorted(l3["l2Vnis"] or []) != expected):
            failures.append(f"{node}: VRF/VNI association")
    return {"timestamp": utc(), "pass": not failures, "failures": failures,
            "neighbors": neighbors, "leaves": leaves, "probes": probes}


def wait_healthy(seconds):
    deadline = time.monotonic() + seconds
    while True:
        result = check()
        if result["pass"] or time.monotonic() >= deadline:
            return result
        time.sleep(0.7)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wait", type=int, default=30)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        require_ready()
        result = wait_healthy(args.wait)
        if args.out:
            write_json(args.out, result)
        print(json.dumps(result, indent=2))
    except ERRORS as error:
        parser.exit(1, describe(error) + "\n")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
