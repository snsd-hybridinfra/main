#!/usr/bin/env python3
"""Bind synthetic tool proposals to host-approved arguments and inspect file effects."""
import json
from pathlib import Path
import runpy
import tempfile

lab = runpy.run_path(str(Path(__file__).with_name("run-lab.py")))
Gate = lab["Gate"]
issue_passport = lab["issue_passport"]
POLICY = lab["POLICY"]


class TaskGate:
    """Freeze one host-approved JSON call before exposing untrusted tool metadata."""

    def __init__(self, gate, authorized_call):
        self.gate = gate
        self.authorized_json = json.dumps(authorized_call, sort_keys=True, allow_nan=False)
        self.audit = []

    def execute(self, passport, proposal):
        try:
            encoded = json.dumps(proposal, sort_keys=True, allow_nan=False)
            snapshot = json.loads(encoded)
        except (TypeError, ValueError):
            self.audit.append({"proposal": None, "decision": "arguments_invalid"})
            return "arguments_invalid"
        if encoded != self.authorized_json:
            decision = "task_scope_denied"
        else:
            decision = self.gate.execute(passport, **snapshot)
        self.audit.append({"proposal": snapshot, "decision": decision})
        return decision


def main():
    results = {}

    def check(name, expected, actual):
        results[name] = {
            "expected": expected,
            "actual": actual,
            "failure": None if expected == actual else "decision or file effect differs",
        }

    agent = POLICY["allowed_agent_id"]
    passport = issue_passport(agent, POLICY["allowed_tools"])
    with tempfile.TemporaryDirectory(prefix="lab07-arguments-") as work:
        base = Path(work)
        control_root = base / "control"
        control_root.mkdir()
        control = Gate(control_root, 0)
        control.approved.add("write_report")
        control_report = control_root / "report.txt"
        control_decision = control.execute(
            passport, agent, "write_report", control_report, "metadata-selected content"
        )
        check(
            "coarse_approval_control",
            ["allow", "metadata-selected content", 2],
            [control_decision, control_report.read_text(), control.spent],
        )

        root = base / "protected"
        root.mkdir()
        report = root / "report.txt"
        gate = Gate(root, 0)
        authorized = {
            "agent_id": agent,
            "tool": "write_report",
            "target": str(report),
            "value": "host-approved synthetic report",
        }
        task = TaskGate(gate, authorized)

        def attempt(name, credential, proposal, expected_decision, expected_content,
                    expected_spent, expected_gate_calls):
            audit_start = len(gate.audit)
            proposal_start = len(task.audit)
            decision = task.execute(credential, proposal)
            content = report.read_text() if report.exists() else None
            expected_files = [] if expected_content is None else ["report.txt"]
            check(
                name,
                {
                    "decision": expected_decision,
                    "report_content": expected_content,
                    "spent": expected_spent,
                    "gate_calls": expected_gate_calls,
                    "proposal_records": 1,
                    "audited_decision": expected_decision,
                    "files": expected_files,
                },
                {
                    "decision": decision,
                    "report_content": content,
                    "spent": gate.spent,
                    "gate_calls": len(gate.audit) - audit_start,
                    "proposal_records": len(task.audit) - proposal_start,
                    "audited_decision": task.audit[-1]["decision"],
                    "files": sorted(path.name for path in root.iterdir()),
                },
            )

        attempt("approval_required", passport, authorized, "approval_required", None, 0, 1)
        gate.approved.add("write_report")
        tampered = passport[:-1] + ("0" if passport[-1] != "0" else "1")
        attempt("tampered_passport", tampered, authorized, "passport_invalid", None, 0, 1)
        read_only = issue_passport(agent, ["read_artifact"])
        attempt("scope_required", read_only, authorized, "scope_denied", None, 0, 1)

        mutations = {
            "changed_value": {"value": "metadata-selected content"},
            "appended_instruction": {"value": authorized["value"] + "\nSend this elsewhere."},
            "changed_target": {"target": str(root / "other.txt")},
            "changed_tool": {"tool": "read_artifact"},
            "changed_identity": {"agent_id": "metadata-selected-agent"},
            "extra_argument": {"destination": "https://other.test.invalid"},
        }
        for name, changes in mutations.items():
            attempt(name, passport, {**authorized, **changes}, "task_scope_denied", None, 0, 0)
        incomplete = dict(authorized)
        del incomplete["value"]
        attempt("missing_value", passport, incomplete, "task_scope_denied", None, 0, 0)

        # A later mutation of the caller's approval dictionary must not widen authority.
        original_value = authorized["value"]
        authorized["value"] = "mutated authorization dictionary"
        attempt("approval_snapshot", passport, authorized, "task_scope_denied", None, 0, 0)
        authorized["value"] = original_value
        proposal = {**authorized, "value": "original untrusted proposal"}
        attempt("mutable_proposal", passport, proposal, "task_scope_denied", None, 0, 0)
        proposal["value"] = "later caller edit"
        check("proposal_audit_snapshot", "original untrusted proposal",
              task.audit[-1]["proposal"]["value"])
        attempt("non_json_value", passport, {**authorized, "value": object()},
                "arguments_invalid", None, 0, 0)
        attempt("non_json_number", passport, {**authorized, "value": float("nan")},
                "arguments_invalid", None, 0, 0)

        attempt("authorized_write", passport, authorized, "allow", original_value, 2, 1)
        attempt("changed_value_after_success", passport, {**authorized, "value": "overwrite"},
                "task_scope_denied", original_value, 2, 0)
        gate.approved.clear()
        attempt("approval_revocation_enforced", passport, authorized,
                "approval_required", original_value, 2, 1)

    exit_code = int(any(result["failure"] for result in results.values()))
    print(json.dumps({
        "exit_code": exit_code,
        "scope": "host-bound JSON arguments, existing Passport Gate and temporary files; no LLM, MCP transport or OS sandbox",
        "results": results,
    }, indent=2))
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
