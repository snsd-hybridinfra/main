#!/usr/bin/env python3
"""Run a deterministic local tool gateway experiment; no LLM or external API."""
from __future__ import annotations

import argparse
import json
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

POLICY = json.loads(Path(__file__).with_name("policy.json").read_text(encoding="utf-8-sig"))


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

    def decide(self, agent_id, tool, target):
        if agent_id != POLICY["allowed_agent_id"]:
            return "identity_denied"
        if tool not in POLICY["allowed_tools"]:
            return "tool_denied"
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
            if (parsed.scheme != allowed["scheme"]
                    or parsed.hostname != allowed["host"]
                    or parsed.port != self.port
                    or parsed.path != allowed["path"]
                    or parsed.query or parsed.fragment
                    or parsed.username or parsed.password):
                return "network_denied"
        if tool in POLICY["approval_required"] and tool not in self.approved:
            return "approval_required"
        return "allow"

    def execute(self, agent_id, tool, target, value=None):
        decision = self.decide(agent_id, tool, target)
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
            outcomes = {
                "read": gate.execute(allowed_agent, "read_artifact", artifact),
                "wrong_identity": gate.execute("unknown-agent", "read_artifact", artifact),
                "unknown_tool": gate.execute(allowed_agent, "shell", "echo test"),
                "path_escape": gate.execute(allowed_agent, "read_artifact", root.parent / "outside.txt"),
                "external_http": gate.execute(allowed_agent, "http_get", "https://example.com/facts"),
                "wrong_local_path": gate.execute(allowed_agent, "http_get", f"http://127.0.0.1:{port}/admin"),
                "local_http": gate.execute(allowed_agent, "http_get", f"http://127.0.0.1:{port}/facts"),
                "wrong_write_target": gate.execute(allowed_agent, "write_report", root / "other.txt", "blocked"),
                "write_without_approval": gate.execute(allowed_agent, "write_report", report, "synthetic report"),
            }
            report_absent_before_approval = not report.exists()
            gate.approved.add("write_report")  # Synthetic approval in test harness.
            outcomes["write_after_approval"] = gate.execute(
                allowed_agent, "write_report", report, "synthetic report"
            )
            outcomes["over_budget"] = gate.execute(allowed_agent, "read_artifact", artifact)
            expected = {
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
            if (outcomes != expected or not report_absent_before_approval
                    or report.read_text(encoding="utf-8") != "synthetic report"
                    or gate.spent != 4):
                raise AssertionError("unexpected policy enforcement result")
            result = {
                "status": "pass",
                "results": outcomes,
                "report_absent_before_approval": report_absent_before_approval,
                "cost_units_spent": gate.spent,
                "cost_units_limit": POLICY["max_cost_units"],
                "audit": gate.audit,
                "runtime": "deterministic local harness; no LLM or external request",
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
