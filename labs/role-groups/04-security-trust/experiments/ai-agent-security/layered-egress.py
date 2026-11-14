#!/usr/bin/env python3
"""Synthetic L4/L7/MCP decision model; not packet enforcement."""
import json
import re
from urllib.parse import urlsplit

UPSTREAM_HOST = "api.test.invalid"
DEFAULT_OPERATIONS = frozenset({"read_facts", "read_api_facts"})
DENIED_OPERATIONS = frozenset({"delete_facts", "delete_api_facts"})


def normalize_operation(operation):
    if not isinstance(operation, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)*", operation):
        return None
    words = re.sub(r"([A-Z])([A-Z][a-z])", r"\1_\2", operation)
    words = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", words)
    return words.lower()


def destination_decision(url):
    if not isinstance(url, str) or re.search(r"[\x00-\x20\x7f\\]", url):
        return "l4_denied"
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError:
        return "l4_denied"
    if (
        parsed.scheme != "https"
        or parsed.username is not None
        or parsed.password is not None
        or parsed.hostname != UPSTREAM_HOST
        or port not in (None, 443)
        or parsed.netloc.lower() not in (UPSTREAM_HOST, f"{UPSTREAM_HOST}:443")
    ):
        return "l4_denied"
    if parsed.path != "/v1/facts" or "?" in url or "#" in url:
        return "l7_denied"
    return "allow"


def decide(identity_valid, url, tool, allowed_operations=DEFAULT_OPERATIONS):
    if not identity_valid:
        return "identity_denied"
    destination = destination_decision(url)
    if destination != "allow":
        return destination
    operation = normalize_operation(tool)
    if operation in DENIED_OPERATIONS or operation not in allowed_operations:
        return "mcp_tool_denied"
    return "allow"

def main():
    cases = {
        "allowed": (True, "https://api.test.invalid/v1/facts", "read_facts", "allow"),
        "identity_invalid": (False, "https://api.test.invalid/v1/facts", "read_facts", "identity_denied"),
        "wrong_destination": (True, "https://other.test.invalid/v1/facts", "read_facts", "l4_denied"),
        "wrong_port": (True, "https://api.test.invalid:8443/v1/facts", "read_facts", "l4_denied"),
        "wrong_path": (True, "https://api.test.invalid/admin", "read_facts", "l7_denied"),
        "query_bypass": (True, "https://api.test.invalid/v1/facts?admin=1", "read_facts", "l7_denied"),
        "wrong_mcp_tool": (True, "https://api.test.invalid/v1/facts", "delete_facts", "mcp_tool_denied"),
        "embedded_credentials": (True, "https://user:pass@api.test.invalid/v1/facts", "read_facts", "l4_denied"),
    }
    results = {name: {"expected": expected, "actual": decide(identity, url, tool)}
               for name, (identity, url, tool, expected) in cases.items()}
    ok = all(v["expected"] == v["actual"] for v in results.values())
    print(json.dumps({"status": "pass" if ok else "fail", "scope": "synthetic Python decisions only; no network, proxy, Kubernetes or MCP server", "results": results}, indent=2))
    if not ok:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
