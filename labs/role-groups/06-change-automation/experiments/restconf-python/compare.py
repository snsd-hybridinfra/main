#!/usr/bin/env python3
"""Read-only IOS XE RESTCONF / SSH interface state comparison."""
import argparse
import base64
import json
import os
import re
import ssl
import subprocess
import sys
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ENDPOINT = "/restconf/data/Cisco-IOS-XE-interfaces-oper:interfaces"
LINE = re.compile(
    r"^(\S+) is (up|down|administratively down), line protocol is (up|down)",
    re.MULTILINE | re.IGNORECASE,
)


def api_rows(payload):
    items = payload["Cisco-IOS-XE-interfaces-oper:interfaces"]["interface"]
    if not isinstance(items, list):
        raise ValueError("RESTCONF interface list is not an array")
    return {item["name"]: item for item in items}


def cli_rows(raw):
    return {
        name: {"admin": "down" if "down" in admin.lower() else "up",
               "oper": oper.lower()}
        for name, admin, oper in LINE.findall(raw.replace("\r", ""))
    }


def normalized_api_status(item):
    admin = item.get("admin-status", "")
    oper = item.get("oper-status", "")
    admin_value = {"if-state-up": "up", "if-state-down": "down"}.get(admin, "unknown")
    oper_value = {"if-oper-state-ready": "up", "if-oper-state-down": "down",
                  "if-oper-state-lower-layer-down": "down"}.get(oper, "unknown")
    return {"admin": admin_value, "oper": oper_value}


def compare(api, cli):
    rows = []
    for name in sorted(set(api) & set(cli)):
        api_state = normalized_api_status(api[name])
        cli_state = cli[name]
        rows.append({
            "name": name,
            "api": api_state,
            "cli": cli_state,
            "match": api_state == cli_state and "unknown" not in api_state.values(),
        })
    return {
        "api_count": len(api),
        "cli_count": len(cli),
        "compared": len(rows),
        "mismatches": sum(not row["match"] for row in rows),
        "api_only": sorted(set(api) - set(cli)),
        "cli_only": sorted(set(cli) - set(api)),
        "rows": rows,
    }


def fetch_restconf(host, port, user, password, context):
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    request = Request(
        f"https://{host}:{port}{ENDPOINT}",
        headers={"Accept": "application/yang-data+json",
                 "Authorization": f"Basic {token}"},
        method="GET",
    )
    with urlopen(request, timeout=20, context=context) as response:
        return json.load(response)


def fetch_cli(host, port, user, password):
    env = os.environ.copy()
    env["SSHPASS"] = password
    command = [
        "sshpass", "-e", "ssh", "-tt",
        "-p", str(port),
        "-o", "StrictHostKeyChecking=accept-new",
        "-o", "ConnectTimeout=15",
        f"{user}@{host}",
    ]
    result = subprocess.run(
        command,
        input="terminal length 0\nshow interfaces\nexit\n",
        text=True,
        capture_output=True,
        env=env,
        timeout=45,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"SSH CLI exited with code {result.returncode}")
    return result.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=os.getenv("IOSXE_HOST", "sandbox-iosxe-latest-1.cisco.com"))
    parser.add_argument("--rest-port", type=int, default=443)
    parser.add_argument("--ssh-port", type=int, default=22)
    parser.add_argument("--ca-bundle", help="Trusted CA bundle for RESTCONF TLS")
    parser.add_argument("--sandbox-insecure-tls", action="store_true",
                        help="Allow the named Cisco public sandbox's mismatched self-signed certificate")
    parser.add_argument("--local-insecure-tls", action="store_true",
                        help="Allow the lab's self-signed certificate for a local synthetic device only")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9.-]+", args.host):
        parser.error("host must be a DNS name or IPv4 address")
    if args.sandbox_insecure_tls and args.host not in (
        "sandbox-iosxe-latest-1.cisco.com",
        "sandbox-iosxe-recomm-1.cisco.com",
    ):
        parser.error("--sandbox-insecure-tls is limited to the two named Cisco public sandboxes")
    if args.local_insecure_tls and args.host not in ("device", "localhost", "127.0.0.1"):
        parser.error("--local-insecure-tls is limited to the local synthetic lab")
    if args.sandbox_insecure_tls and args.local_insecure_tls:
        parser.error("choose one TLS exception mode")
    user = os.getenv("IOSXE_USER")
    password = os.getenv("IOSXE_PASSWORD")
    if not user or not password:
        parser.error("set IOSXE_USER and IOSXE_PASSWORD in the environment")
    context = (ssl._create_unverified_context()
               if args.sandbox_insecure_tls or args.local_insecure_tls
               else ssl.create_default_context(cafile=args.ca_bundle))
    try:
        payload = fetch_restconf(args.host, args.rest_port, user, password, context)
        api = api_rows(payload)
        cli = cli_rows(fetch_cli(args.host, args.ssh_port, user, password))
        result = compare(api, cli)
        result["collected_at_utc"] = datetime.now(timezone.utc).isoformat()
        result["host"] = args.host
        result["restconf_endpoint"] = ENDPOINT
        result["validation_scope"] = ("local-synthetic-device"
                                      if args.local_insecure_tls else "external-device")
        result["status"] = ("pass" if result["compared"] and not result["mismatches"]
                            else "inconclusive" if not result["compared"] else "fail")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "pass" else 1
    except HTTPError as exc:
        print(f"RESTCONF HTTP {exc.code}; comparison not run.", file=sys.stderr)
    except (URLError, ssl.SSLError, subprocess.TimeoutExpired, RuntimeError,
            ValueError, KeyError, OSError) as exc:
        print(f"Collection failed: {type(exc).__name__}; comparison not run.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
