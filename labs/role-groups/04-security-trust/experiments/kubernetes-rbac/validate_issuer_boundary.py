#!/usr/bin/env python3
"""Validate synthetic issuerRef kind, name, and namespace boundaries locally."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def decide(policy: dict, case: dict) -> tuple[str, str]:
    if case.get("namespace") != policy["namespace"]:
        return "deny", "namespace_mismatch"
    issuer_ref = case.get("issuer_ref", {})
    kind = issuer_ref.get("kind")
    name = issuer_ref.get("name")
    if not kind:
        return "deny", "kind_required"
    allowed = any(item["kind"] == kind and item["name"] == name for item in policy["allowed_issuers"])
    if not allowed:
        return "deny", "issuer_kind_or_name_not_approved"
    return "allow", "approved_exact_issuer"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="issuer-boundary-cases.json")
    parser.add_argument("--evidence")
    args = parser.parse_args()

    input_path = Path(args.input)
    raw = input_path.read_bytes()
    data = json.loads(raw)
    results = []
    for case in data["cases"]:
        actual, reason = decide(data["approval_policy"], case)
        results.append({
            "name": case["name"],
            "issuer_ref": case["issuer_ref"],
            "namespace": case["namespace"],
            "expected": case["expected"],
            "actual": actual,
            "reason": reason,
            "passed": actual == case["expected"],
        })

    passed = all(item["passed"] for item in results)
    report = {
        "tested_at": datetime.now(timezone.utc).isoformat(),
        "status": "passed" if passed else "failed",
        "source": data["source"],
        "scope": "synthetic issuer approval-policy evaluation",
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "summary": {
            "total": len(results),
            "passed": sum(item["passed"] for item in results),
            "allowed": sum(item["actual"] == "allow" for item in results),
            "denied": sum(item["actual"] == "deny" for item in results),
        },
        "results": results,
        "not_validated": [
            "AWS Private CA Connector for Kubernetes or cert-manager runtime",
            "affected and fixed connector versions",
            "certificate or subordinate CA issuance",
            "upgrade and certificate renewal behavior",
        ],
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.evidence:
        Path(args.evidence).write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
