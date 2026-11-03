#!/usr/bin/env python3
"""Synthetic L4/L7/MCP decision model; not packet enforcement."""
import json
from urllib.parse import urlsplit

def decide(identity_valid, url, tool):
    if not identity_valid:
        return "identity_denied"
    p = urlsplit(url)
    if p.scheme != "https" or p.username is not None or p.password is not None or (p.hostname, p.port or 443) != ("api.test.invalid", 443):
        return "l4_denied"
    if p.path != "/v1/facts" or p.query or p.fragment:
        return "l7_denied"
    if tool != "read_facts":
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
