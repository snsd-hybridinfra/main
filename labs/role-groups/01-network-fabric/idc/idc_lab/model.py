"""Read the single topology used by the four participating roles."""
import ipaddress
import json
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
ROOT = LAB.parents[3]
OUT = ROOT / ".runtime/idc"
STATE = Path("/run/idc-resilience")
DATA = json.loads((LAB / "topology.json").read_text())
ROUTERS, HOSTS, LINKS, VLANS = (DATA[key] for key in ("routers", "hosts", "links", "vlans"))
NODES = (*ROUTERS, *HOSTS)
LEAVES = tuple(node for node in ROUTERS if "host" in ROUTERS[node])
SHARED = DATA["shared_vlan"]
VRF, L3_VNI, L3_BRIDGE = (DATA[key] for key in ("vrf", "l3_vni", "l3_bridge"))


def interfaces(node):
    for link in LINKS:
        a, b = link["a"], link["b"]
        if a[0] == node:
            yield a[1], a[2], *b
        elif b[0] == node:
            yield b[1], b[2], *a


def address(cidr):
    return str(ipaddress.ip_interface(cidr).ip)


def prefix(cidr):
    return str(ipaddress.ip_interface(cidr).network)


def fabric_links(node):
    return [link for link in interfaces(node) if link[1]]


def peers(node, family):
    return [(address(remote_ip) if family == "ipv4" else ROUTERS[remote]["loopback"],
             ROUTERS[remote]["asn"]) for _, _, remote, _, remote_ip in fabric_links(node)]


def leaf_vlans(node):
    return SHARED, ROUTERS[node]["local_vlan"]


def local_prefix(node):
    return prefix(VLANS[ROUTERS[node]["local_vlan"]]["gateway"])


def probe_ips(path):
    vlans = (SHARED, SHARED) if path == "l2" else tuple(ROUTERS[node]["local_vlan"] for node in LEAVES)
    return tuple(address(HOSTS[host][vlan]) for host, vlan in zip(HOSTS, vlans, strict=True))
