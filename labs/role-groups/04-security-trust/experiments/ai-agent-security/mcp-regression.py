#!/usr/bin/env python3
"""Exercise a synthetic MCP decision model and an in-memory management API."""
import json
from pathlib import Path
import runpy

egress = runpy.run_path(str(Path(__file__).with_name("layered-egress.py")))
decide = egress["decide"]
destination_decision = egress["destination_decision"]
default_operations = egress["DEFAULT_OPERATIONS"]
normalize_operation = egress["normalize_operation"]
ALLOWED_URL = "https://api.test.invalid/v1/facts"
OTHER_URL = "https://api.test.invalid:443/v1/facts"


class MockRegistry:
    """Local API model. Authentication context is supplied by a test fixture."""

    def __init__(self):
        self.servers = {}
        self.roles = {"lab-admin": "admin", "lab-viewer": "viewer"}

    def put_server(self, principal, name, url):
        role = self.roles.get(principal)
        if role is None:
            return 401
        if role != "admin":
            return 403
        if destination_decision(url) != "allow":
            return 400
        created = name not in self.servers
        self.servers[name] = url
        return 201 if created else 200


class MockToolRouter:
    """Use host-assigned server IDs and host policy, with synthetic dispatch receipts."""

    def __init__(self, registry, provider_bindings):
        self.registry = registry
        self.provider_bindings = dict(provider_bindings)
        self.executions = []

    def call(self, identity_valid, server, tool):
        url = self.registry.servers.get(server)
        if url is None:
            return "provider_unknown"
        decision = decide(identity_valid, url, tool)
        if decision != "allow":
            return decision
        operation = normalize_operation(tool)
        if self.provider_bindings.get(operation) != server:
            return "provider_denied"
        self.executions.append({"server": server, "operation": operation, "url": url})
        return "allow"


def main():
    registry = MockRegistry()
    results = {}

    def check(name, expected, actual):
        results[name] = {
            "expected": expected,
            "actual": actual,
            "failure": None if expected == actual else "decision or side effect differs",
        }

    def register(name, principal, url, expected_code, expected_url):
        code = registry.put_server(principal, "facts", url)
        check(name, [expected_code, expected_url], [code, registry.servers.get("facts")])

    blocked_urls = {
        "loopback": "https://127.0.0.1/v1/facts",
        "private": "https://192.168.0.2/v1/facts",
        "link_local": "https://169.254.0.2/v1/facts",
        "ipv6_loopback": "https://[::1]/v1/facts",
        "internal_name": "https://internal.test.invalid/v1/facts",
        "userinfo": "https://api.test.invalid@internal.test.invalid/v1/facts",
        "port_zero": "https://api.test.invalid:0/v1/facts",
        "malformed_port": "https://api.test.invalid:bad/v1/facts",
        "malformed_ipv6": "https://[::1/v1/facts",
        "wrong_scheme": "http://api.test.invalid/v1/facts",
        "nat64_private": "https://[64:ff9b::c0a8:2]/v1/facts",
        "nat64_link_local": "https://[64:ff9b::a9fe:2]/v1/facts",
    }

    register("anonymous_create", None, ALLOWED_URL, 401, None)
    register("viewer_create", "lab-viewer", ALLOWED_URL, 403, None)
    register("admin_internal_create", "lab-admin", blocked_urls["private"], 400, None)
    register("admin_create", "lab-admin", ALLOWED_URL, 201, ALLOWED_URL)
    register("viewer_update", "lab-viewer", OTHER_URL, 403, ALLOWED_URL)
    for name, url in blocked_urls.items():
        check(f"egress_{name}", "l4_denied", decide(True, url, "read_facts"))
        register(f"registry_{name}", "lab-admin", url, 400, ALLOWED_URL)
    register("admin_update", "lab-admin", OTHER_URL, 200, OTHER_URL)

    operations = {
        "read_facts": "allow",
        "ReadAPIFacts": "allow",
        "delete_facts": "mcp_tool_denied",
        "DeleteAPIFacts": "mcp_tool_denied",
        "DELETE_API_FACTS": "mcp_tool_denied",
        "deleteApiFacts": "mcp_tool_denied",
        "unknown_operation": "mcp_tool_denied",
    }
    for operation, expected in operations.items():
        check(f"baseline_{operation}", expected, decide(True, ALLOWED_URL, operation))

    check("canonical_acronym", "delete_api_facts", normalize_operation("DeleteAPIFacts"))
    check(
        "deny_wins_over_allow",
        "mcp_tool_denied",
        decide(True, ALLOWED_URL, "DeleteAPIFacts", default_operations | {"delete_api_facts"}),
    )
    check("temporary_lockdown", "mcp_tool_denied", decide(True, ALLOWED_URL, "ReadAPIFacts", frozenset()))
    for operation, expected in operations.items():
        check(f"restored_{operation}", expected, decide(True, ALLOWED_URL, operation, default_operations))
    check("restored_egress", "l4_denied", decide(True, blocked_urls["private"], "read_facts"))
    register("restored_viewer_update", "lab-viewer", ALLOWED_URL, 403, OTHER_URL)
    register("restored_admin_internal_update", "lab-admin", blocked_urls["private"], 400, OTHER_URL)
    register("restored_admin_update", "lab-admin", ALLOWED_URL, 200, ALLOWED_URL)

    check("second_provider_create", 201, registry.put_server("lab-admin", "other-facts", ALLOWED_URL))
    router = MockToolRouter(registry, {"read_facts": "facts", "read_api_facts": "facts"})

    def route(name, identity, server, tool, expected_decision, expected_executions):
        start = len(router.executions)
        before = dict(registry.servers)
        decision = router.call(identity, server, tool)
        check(
            name,
            [expected_decision, expected_executions, True],
            [decision, router.executions[start:], registry.servers == before],
        )

    route("bound_provider", True, "facts", "read_facts", "allow", [
        {"server": "facts", "operation": "read_facts", "url": ALLOWED_URL},
    ])
    route("bound_provider_acronym", True, "facts", "ReadAPIFacts", "allow", [
        {"server": "facts", "operation": "read_api_facts", "url": ALLOWED_URL},
    ])
    route("same_name_other_provider", True, "other-facts", "read_facts", "provider_denied", [])
    route("normalized_name_other_provider", True, "other-facts", "ReadAPIFacts", "provider_denied", [])
    route("unregistered_provider", True, "unknown-facts", "read_facts", "provider_unknown", [])
    route("provider_identity_invalid", False, "facts", "read_facts", "identity_denied", [])
    route("provider_denied_operation", True, "facts", "DeleteAPIFacts", "mcp_tool_denied", [])
    route("provider_malformed_operation", True, "facts", "read facts", "mcp_tool_denied", [])

    # The host can revoke a binding without trusting advertised metadata.
    del router.provider_bindings["read_api_facts"]
    route("provider_binding_revoked", True, "facts", "ReadAPIFacts", "provider_denied", [])
    router.provider_bindings["read_api_facts"] = "facts"
    route("provider_binding_restored", True, "facts", "ReadAPIFacts", "allow", [
        {"server": "facts", "operation": "read_api_facts", "url": ALLOWED_URL},
    ])

    del registry.servers["facts"]
    route("registered_provider_removed", True, "facts", "read_facts", "provider_unknown", [])
    register("provider_registration_restored", "lab-admin", ALLOWED_URL, 201, ALLOWED_URL)
    # Inject stale registry state to verify the dispatch boundary rechecks egress.
    registry.servers["facts"] = blocked_urls["private"]
    route("provider_egress_rechecked", True, "facts", "read_facts", "l4_denied", [])
    register("provider_endpoint_restored", "lab-admin", ALLOWED_URL, 200, ALLOWED_URL)
    route("provider_recovery", True, "facts", "read_facts", "allow", [
        {"server": "facts", "operation": "read_facts", "url": ALLOWED_URL},
    ])

    exit_code = int(any(result["failure"] for result in results.values()))
    print(json.dumps({"exit_code": exit_code, "results": results}, indent=2))
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
