"""Scoped Leaf1 policy edits shared by failure injection and change validation."""
from .model import ROUTERS, peers
from .runtime import checked_cli, vty

NODE = "leaf1"
REMOTE = ROUTERS["leaf2"]["loopback"] + "/32"
BASE_HOPS = sorted(addr for addr, _ in peers(NODE, "ipv4"))
SPINE1, SPINE2 = (addr for addr, _ in peers(NODE, "ipv4"))
ASN = ROUTERS[NODE]["asn"]
POLICY_SLOT = "ip prefix-list FABRIC-LOOPBACKS seq 5"
CANDIDATES = {"harmless": "192.0.2.250/32", "break-vtep": REMOTE}


def running():
    result = vty(NODE, "show running-config")
    checked_cli(result)
    return result.stdout


def require_free_slot():
    if POLICY_SLOT + " " in running():
        raise RuntimeError("Sequence 5 is occupied. Restore the lab baseline.")


def config(*commands):
    checked_cli(vty(NODE, "configure terminal", *commands, timeout=8))


def change_policy(candidate, apply):
    command = f"{POLICY_SLOT} deny {CANDIDATES[candidate]}"
    config(command if apply else "no " + command)
    for peer, _ in peers(NODE, "ipv4"):
        checked_cli(vty(NODE, f"clear bgp ipv4 unicast {peer} soft in"))
