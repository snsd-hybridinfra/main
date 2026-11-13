#!/usr/bin/env python3
"""Evaluate a bounded subset of AWS-style trust, role, and session policies locally."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def values(value: str | list[str]) -> list[str]:
    return value if isinstance(value, list) else [value]


def matches(statement: dict, action: str, resource: str) -> bool:
    actions = values(statement.get("Action", []))
    resources = values(statement.get("Resource", "*"))
    return any(fnmatch.fnmatchcase(action, pattern) for pattern in actions) and any(
        fnmatch.fnmatchcase(resource, pattern) for pattern in resources
    )


def policy_decision(policy: dict, action: str, resource: str) -> tuple[str, list[str]]:
    matched = [statement for statement in policy["Statement"] if matches(statement, action, resource)]
    deny_sids = [statement.get("Sid", "unnamed") for statement in matched if statement["Effect"] == "Deny"]
    if deny_sids:
        return "explicit_deny", deny_sids
    allow_sids = [statement.get("Sid", "unnamed") for statement in matched if statement["Effect"] == "Allow"]
    if allow_sids:
        return "allow", allow_sids
    return "implicit_deny", []


def trust_allows(policy: dict, caller: str) -> tuple[bool, list[str]]:
    matched = []
    for statement in policy["Statement"]:
        principals = values(statement.get("Principal", {}).get("AWS", []))
        actions = values(statement.get("Action", []))
        if statement["Effect"] == "Allow" and caller in principals and "sts:AssumeRole" in actions:
            matched.append(statement.get("Sid", "unnamed"))
    return bool(matched), matched


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", default=".")
    parser.add_argument("--evidence")
    args = parser.parse_args()

    base = Path(args.directory)
    paths = {
        "caller": base / "caller-permissions.example.json",
        "trust": base / "trust-policy.example.json",
        "role": base / "role-permissions.example.json",
        "session": base / "session-policy.example.json",
        "scenarios": base / "scenarios.json",
    }
    raw = {name: path.read_bytes() for name, path in paths.items()}
    documents = {name: json.loads(content) for name, content in raw.items()}
    results = []

    for scenario in documents["scenarios"]["assume_role"]:
        caller_decision, caller_sids = policy_decision(
            documents["caller"], "sts:AssumeRole", scenario["role_arn"]
        )
        trust_decision, trust_sids = trust_allows(documents["trust"], scenario["caller_arn"])
        allowed = caller_decision == "allow" and trust_decision
        results.append(
            {
                "name": scenario["name"],
                "type": "assume_role",
                "allowed": allowed,
                "expected_allowed": scenario["expected_allowed"],
                "caller_policy": caller_decision,
                "caller_policy_sids": caller_sids,
                "trust_policy_sids": trust_sids,
                "passed": allowed == scenario["expected_allowed"],
            }
        )

    for scenario in documents["scenarios"]["session_actions"]:
        role_decision, role_sids = policy_decision(
            documents["role"], scenario["action"], scenario["resource"]
        )
        session_decision, session_sids = policy_decision(
            documents["session"], scenario["action"], scenario["resource"]
        )
        if role_decision == "explicit_deny" or session_decision == "explicit_deny":
            final_decision = "explicit_deny"
        elif role_decision == "allow" and session_decision == "allow":
            final_decision = "allow"
        else:
            final_decision = "implicit_deny"
        allowed = final_decision == "allow"
        results.append(
            {
                "name": scenario["name"],
                "type": "session_action",
                "action": scenario["action"],
                "resource": scenario["resource"],
                "allowed": allowed,
                "expected_allowed": scenario["expected_allowed"],
                "role_decision": role_decision,
                "role_policy_sids": role_sids,
                "session_decision": session_decision,
                "session_policy_sids": session_sids,
                "final_decision": final_decision,
                "passed": allowed == scenario["expected_allowed"],
            }
        )

    passed = all(result["passed"] for result in results)
    report = {
        "tested_at": datetime.now(timezone.utc).isoformat(),
        "scope": "local-policy-evaluation-only",
        "input_sha256": {
            name: hashlib.sha256(content).hexdigest() for name, content in raw.items()
        },
        "results": results,
        "summary": {
            "total": len(results),
            "allowed": sum(result["allowed"] for result in results),
            "denied": sum(not result["allowed"] for result in results),
            "passed": sum(result["passed"] for result in results),
        },
        "status": "passed" if passed else "failed",
        "not_validated": [
            "AWS or Azure runtime",
            "STS token issuance and expiration",
            "credential compromise or rotation",
            "Azure resource locks",
        ],
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.evidence:
        Path(args.evidence).write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())