#!/usr/bin/env python3
"""Run a deterministic local agent authorization experiment; no LLM or external API."""
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

POLICY = json.loads(Path(__file__).with_name("policy.json").read_text(encoding="utf-8-sig"))
TEST_SIGNING_KEY = b"local-lab-hmac-key-not-for-production"


def _encode(payload):
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def issue_passport(agent_id, allowed_tools):
    payload = {
        "key_id": POLICY["passport_key_id"],
        "agent_id": agent_id,
        "allowed_tools": sorted(allowed_tools),
    }
    encoded = _encode(payload)
    signature = hmac.new(TEST_SIGNING_KEY, encoded.encode(), hashlib.sha256).hexdigest()
    return f"{encoded}.{signature}"


def verify_passport(passport, claimed_agent_id):
    try:
        encoded, signature = passport.split(".", 1)
        expected = hmac.new(TEST_SIGNING_KEY, encoded.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return None
        padded = encoded + "=" * (-len(encoded) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))
        if payload["key_id"] != POLICY["passport_key_id"]:
            return None
        if payload["agent_id"] != claimed_agent_id:
            return None
        if not isinstance(payload["allowed_tools"], list):
            return None
        return payload
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return None


class FactsHandler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def do_GET(self):
        if self.path != "/facts":
            self.send_error(404)
            return
        body = b'{"source":"local-fixture","fact":"synthetic"}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class Gate:
    def __init__(self, root, port):
        self.root = root.resolve()
        self.port = port
        self.spent = 0
        self.approved = set()
        self.audit = []

    def decide(self, passport, agent_id, tool, target):
        if not passport:
            return "passport_required"
        claims = verify_passport(passport, agent_id)
        if claims is None:
            return "passport_invalid"
        if agent_id in POLICY["revoked_agent_ids"]:
            return "identity_revoked"
        if agent_id != POLICY["allowed_agent_id"]:
            return "identity_denied"
        if tool not in POLICY["allowed_tools"]:
            return "tool_denied"
        if tool not in claims["allowed_tools"]:
            return "scope_denied"
        cost = POLICY["cost_units"][tool]
        if self.spent + cost > POLICY["max_cost_units"]:
            return "budget_exceeded"
        if tool in ("read_artifact", "write_report"):
            path = Path(target).resolve()
            if not path.is_relative_to(self.root):
                return "path_denied"
            if tool == "write_report" and path != self.root / "report.txt":
                return "path_denied"
        if tool == "http_get":
            parsed = urlparse(target)
            allowed = POLICY["allowed_http"]
            if (
                parsed.scheme != allowed["scheme"]
                or parsed.hostname != allowed["host"]
                or parsed.port != self.port
                or parsed.path != allowed["path"]
                or parsed.query
                or parsed.fragment
                or parsed.username
                or parsed.password
            ):
                return "network_denied"
        if tool in POLICY["approval_required"] and tool not in self.approved:
            return "approval_required"
        return "allow"

    def execute(self, passport, agent_id, tool, target, value=None):
        decision = self.decide(passport, agent_id, tool, target)
        if decision == "allow":
            if tool == "read_artifact":
                Path(target).read_text(encoding="utf-8")
            elif tool == "http_get":
                with urlopen(target, timeout=2) as response:
                    json.load(response)
            elif tool == "write_report":
                Path(target).write_text(value, encoding="utf-8")
            self.spent += POLICY["cost_units"][tool]
        self.audit.append({"agent_id": agent_id, "tool": tool, "decision": decision})
        return decision


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence")
    args = parser.parse_args()
    allowed_agent = POLICY["allowed_agent_id"]

    with tempfile.TemporaryDirectory(prefix="lab07-agent-") as work:
        root = Path(work)
        artifact = root / "facts.txt"
        artifact.write_text("synthetic source\n", encoding="utf-8")
        report = root / "report.txt"
        server = ThreadingHTTPServer(("127.0.0.1", 0), FactsHandler)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            port = server.server_port
            gate = Gate(root, port)
            full_passport = issue_passport(allowed_agent, POLICY["allowed_tools"])
            unknown_passport = issue_passport("unknown-agent", POLICY["allowed_tools"])
            revoked_passport = issue_passport("revoked-agent-01", POLICY["allowed_tools"])
            read_only_passport = issue_passport(allowed_agent, ["read_artifact"])
            tampered_passport = full_passport[:-1] + ("0" if full_passport[-1] != "0" else "1")

            outcomes = {
                "missing_passport": gate.execute(None, allowed_agent, "read_artifact", artifact),
                "tampered_passport": gate.execute(tampered_passport, allowed_agent, "read_artifact", artifact),
                "revoked_passport": gate.execute(revoked_passport, "revoked-agent-01", "read_artifact", artifact),
                "scope_exceeded": gate.execute(read_only_passport, allowed_agent, "http_get", f"http://127.0.0.1:{port}/facts"),
                "read": gate.execute(full_passport, allowed_agent, "read_artifact", artifact),
                "wrong_identity": gate.execute(unknown_passport, "unknown-agent", "read_artifact", artifact),
                "unknown_tool": gate.execute(full_passport, allowed_agent, "shell", "echo test"),
                "path_escape": gate.execute(full_passport, allowed_agent, "read_artifact", root.parent / "outside.txt"),
                "external_http": gate.execute(full_passport, allowed_agent, "http_get", "https://example.com/facts"),
                "wrong_local_path": gate.execute(full_passport, allowed_agent, "http_get", f"http://127.0.0.1:{port}/admin"),
                "local_http": gate.execute(full_passport, allowed_agent, "http_get", f"http://127.0.0.1:{port}/facts"),
                "wrong_write_target": gate.execute(full_passport, allowed_agent, "write_report", root / "other.txt", "blocked"),
                "write_without_approval": gate.execute(full_passport, allowed_agent, "write_report", report, "synthetic report"),
            }
            report_absent_before_approval = not report.exists()
            gate.approved.add("write_report")
            outcomes["write_after_approval"] = gate.execute(full_passport, allowed_agent, "write_report", report, "synthetic report")
            outcomes["over_budget"] = gate.execute(full_passport, allowed_agent, "read_artifact", artifact)
            expected = {
                "missing_passport": "passport_required",
                "tampered_passport": "passport_invalid",
                "revoked_passport": "identity_revoked",
                "scope_exceeded": "scope_denied",
                "read": "allow",
                "wrong_identity": "identity_denied",
                "unknown_tool": "tool_denied",
                "path_escape": "path_denied",
                "external_http": "network_denied",
                "wrong_local_path": "network_denied",
                "local_http": "allow",
                "wrong_write_target": "path_denied",
                "write_without_approval": "approval_required",
                "write_after_approval": "allow",
                "over_budget": "budget_exceeded",
            }
            if (
                outcomes != expected
                or not report_absent_before_approval
                or report.read_text(encoding="utf-8") != "synthetic report"
                or gate.spent != 4
            ):
                raise AssertionError("unexpected policy enforcement result")
            result = {
                "status": "pass",
                "source": {
                    "servicenow_ai_passport": "https://newsroom.servicenow.com/press-releases/details/2026/ServiceNow-advances-its-operational-harness-for-enterprise-AI-with-AI-Passport-and-expanded-governance-capabilities/default.aspx",
                    "published_at": "2026-10-15",
                },
                "credential_model": "local HMAC-signed test passport; not ServiceNow AI Passport",
                "results": outcomes,
                "report_absent_before_approval": report_absent_before_approval,
                "cost_units_spent": gate.spent,
                "cost_units_limit": POLICY["max_cost_units"],
                "audit": gate.audit,
                "runtime": "deterministic local harness; no LLM or external request",
                "not_validated": [
                    "ServiceNow AI Passport, Super Intelligence Control Tower, or NVIDIA OpenShell",
                    "asymmetric signatures, enterprise PKI, IdP, CMDB, GRC, or distributed revocation",
                    "real AI agent, MCP server, model inference, or operating-system sandbox",
                ],
            }
            rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
            if args.evidence:
                Path(args.evidence).write_text(rendered, encoding="utf-8", newline="\n")
            print(rendered, end="")
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=2)


if __name__ == "__main__":
    main()
