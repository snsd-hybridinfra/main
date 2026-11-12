"""Export or seed the NetBox 4.5 inventory from the shared IDC topology."""
import argparse
import json
import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .model import DATA, HOSTS, L3_VNI, LEAVES, LINKS, NODES, ROUTERS, SHARED, VLANS, VRF
from .model import interfaces, leaf_vlans, prefix
from .verify import write_json

SITE = "idc-lab"
REMOTE_SITE = "idc-lab-remote"
WAN = "IDC-LAB-WAN-01"


def inventory():
    ports = {node: {} for node in NODES}
    prefixes = set()
    for link in LINKS:
        for node, port, cidr in (link["a"], link["b"]):
            ports[node][port] = {"type": "1000base-t", "address": cidr, "vrf": None}
            if cidr:
                prefixes.add((prefix(cidr), "global"))
    for node, info in ROUTERS.items():
        cidr = info["loopback"] + "/32"
        ports[node]["lo"] = {"type": "virtual", "address": cidr, "vrf": None}
        prefixes.add((cidr, "global"))
    for node in LEAVES:
        for vlan in leaf_vlans(node):
            gateway = VLANS[vlan]["gateway"]
            ports[node][f"br{vlan}"] = {"type": "virtual", "address": gateway, "vrf": VRF,
                                      "vlan": int(vlan), "role": "anycast" if vlan == SHARED else None}
            prefixes.add((prefix(gateway), VRF))
    for node, vlans in HOSTS.items():
        port = next(interfaces(node))[0]
        for vlan, cidr in vlans.items():
            ports[node][f"{port}.{vlan}"] = {"type": "virtual", "address": cidr, "vrf": VRF, "vlan": int(vlan)}
    return {"site": SITE, "remote_site": REMOTE_SITE, "vrf": VRF, "l3_vni": L3_VNI,
            "vlans": VLANS, "ports": ports,
            "prefixes": [{"prefix": cidr, "vrf": domain} for cidr, domain in sorted(prefixes)],
            "cables": [{"label": f"IDC-LAB-{link['id']}", "a": link["a"][:2], "b": link["b"][:2]}
                       for link in LINKS],
            "circuits": [{"cid": WAN, "status": "planned", "a": SITE, "z": REMOTE_SITE}]}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *_):
        return None


def equal(observed, wanted):
    if isinstance(wanted, list):
        return isinstance(observed, list) and len(observed) == len(wanted) and all(
            equal(item, value) for item, value in zip(observed, wanted, strict=True))
    if isinstance(wanted, dict):
        return isinstance(observed, dict) and all(equal(observed.get(k), v) for k, v in wanted.items())
    if isinstance(observed, dict):
        return any(key in observed and observed[key] == wanted for key in ("id", "value"))
    return observed == wanted


class NetBox:
    def __init__(self, url, token, scheme="Bearer"):
        parts = urlsplit(url)
        if parts.scheme not in ("http", "https") or not parts.hostname or parts.username or parts.query or parts.fragment:
            raise ValueError("NETBOX_URL must be a base HTTP(S) URL without embedded credentials.")
        self.url, self.token, self.scheme = url.rstrip("/") + "/api/", token, scheme
        self.client = build_opener(NoRedirect())
        self.created = self.reused = 0

    def request(self, verb, endpoint, query=None, payload=None):
        url = self.url + endpoint.strip("/") + "/"
        if query:
            url += "?" + urlencode({"limit": 100, **query})
        data = json.dumps(payload).encode() if payload is not None else None
        request = Request(url, method=verb, data=data, headers={
            "Authorization": f"{self.scheme} {self.token}",
            "Accept": "application/json", "Content-Type": "application/json",
        })
        try:
            with self.client.open(request, timeout=15) as response:
                return json.load(response)
        except HTTPError as error:
            message = error.read(1000).decode(errors="replace").replace(self.token, "[redacted]")
            raise RuntimeError(f"{verb} {endpoint}: HTTP {error.code} {message}") from error

    def ensure(self, endpoint, query, payload, identity=None):
        result = self.request("GET", endpoint, query=query)
        if result["next"]:
            raise RuntimeError(f"Ambiguous result for {endpoint}: {query}")
        matches = [row for row in result["results"]
                   if identity is None or all(equal(row.get(key), value) for key, value in identity.items())]
        if len(matches) > 1:
            raise RuntimeError(f"Duplicate NetBox objects at {endpoint}: {query}")
        if matches:
            record = matches[0]
            drift = [key for key, value in payload.items() if not equal(record.get(key), value)]
            if drift:
                raise RuntimeError(f"NetBox drift at {endpoint}: {query} fields {drift}")
            self.reused += 1
        else:
            record = self.request("POST", endpoint, payload=payload)
            self.created += 1
        return record["id"]


def seed(api, plan):
    def named(endpoint, slug, **extra):
        return api.ensure(endpoint, {"slug": slug}, {"name": slug, "slug": slug, **extra})

    site = named("dcim/sites", SITE, status="active")
    remote = named("dcim/sites", REMOTE_SITE, status="planned")
    manufacturer = named("dcim/manufacturers", "idc-lab-generic")
    device_type = api.ensure("dcim/device-types", {"slug": "idc-lab-linux"},
                             {"manufacturer": manufacturer, "model": "IDC Lab Linux", "slug": "idc-lab-linux"})
    roles = {role: named("dcim/device-roles", f"idc-lab-{role}", color=color)
             for role, color in (("spine", "3f51b5"), ("leaf", "009688"), ("host", "607d8b"))}
    target = f"{DATA['rt_asn']}:{L3_VNI}"
    rt = api.ensure("ipam/route-targets", {"name": target}, {"name": target})
    name = "IDC-LAB-" + VRF
    vrf = api.ensure("ipam/vrfs", {"name": name},
                     {"name": name, "enforce_unique": False, "import_targets": [rt], "export_targets": [rt]})
    group = named("ipam/vlan-groups", "idc-lab-vlans", scope_type="dcim.site", scope_id=site)
    vlan_prefixes = {}
    for tag, row in VLANS.items():
        vid = int(tag)
        vlan_prefixes[prefix(row["gateway"])] = api.ensure(
            "ipam/vlans", {"group_id": group, "vid": vid},
            {"group": group, "vid": vid, "name": f"VLAN{vid}", "status": "active",
             "description": f"L2 VNI {row['vni']}"})
    for item in plan["prefixes"]:
        cidr = item["prefix"]
        domain = vrf if item["vrf"] == VRF else None
        api.ensure("ipam/prefixes", {"prefix": cidr},
                   {"prefix": cidr, "vrf": domain, "scope_type": "dcim.site", "scope_id": site,
                    "vlan": vlan_prefixes.get(cidr), "status": "active"}, identity={"vrf": domain})
    port_ids = {}
    for node, ports in plan["ports"].items():
        role = "leaf" if node in LEAVES else "spine" if node in ROUTERS else "host"
        name = f"{SITE}-{node}"
        device = api.ensure("dcim/devices", {"name": name, "site_id": site},
                            {"name": name, "device_type": device_type, "role": roles[role],
                             "site": site, "status": "active"})
        for port, data in ports.items():
            domain = vrf if data["vrf"] else None
            body = {"name": port, "type": data["type"], "device": device, "vrf": domain}
            if data.get("vlan"):
                body["description"] = f"VLAN {data['vlan']}"
            iface = api.ensure("dcim/interfaces", {"device_id": device, "name": port}, body)
            port_ids[(node, port)] = iface
            if cidr := data["address"]:
                body = {"address": cidr, "vrf": domain, "status": "active",
                        "assigned_object_type": "dcim.interface", "assigned_object_id": iface}
                if data.get("role"):
                    body["role"] = data["role"]
                api.ensure("ipam/ip-addresses", {"address": cidr}, body,
                           identity={"vrf": domain, "assigned_object_id": iface})
    for link in plan["cables"]:
        body = {"label": link["label"], "status": "connected"}
        for side in ("a", "b"):
            body[f"{side}_terminations"] = [
                {"object_type": "dcim.interface", "object_id": port_ids[tuple(link[side])]}
            ]
        api.ensure("dcim/cables", {"label": link["label"]}, body)
    provider = named("circuits/providers", "idc-lab-carrier")
    circuit_type = named("circuits/circuit-types", "idc-lab-wan")
    circuit = api.ensure("circuits/circuits", {"cid": WAN, "provider_id": provider},
                         {"cid": WAN, "provider": provider, "type": circuit_type, "status": "planned",
                          "description": "Synthetic inventory-only circuit"})
    for side, terminal in (("A", site), ("Z", remote)):
        api.ensure("circuits/circuit-terminations", {"circuit_id": circuit, "term_side": side},
                   {"circuit": circuit, "term_side": side, "termination_type": "dcim.site",
                    "termination_id": terminal})
    return {"created": api.created, "reused": api.reused, "devices": len(NODES),
            "interfaces": len(port_ids), "cables": len(plan["cables"]), "circuits": len(plan["circuits"])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--legacy-token", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        plan = inventory()
        if args.apply:
            url, token = os.environ.get("NETBOX_URL"), os.environ.get("NETBOX_TOKEN")
            if not url or not token:
                raise ValueError("Set NETBOX_URL and NETBOX_TOKEN in this shell.")
            plan = seed(NetBox(url, token, "Token" if args.legacy_token else "Bearer"), plan)
        if args.out:
            write_json(args.out, plan)
        print(json.dumps(plan, indent=2))
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        parser.exit(1, str(error) + "\n")


if __name__ == "__main__":
    main()
