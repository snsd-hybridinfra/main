#!/usr/bin/env python3
"""Validate ZT-AUTO-001 catalogs, references, graph, and execution boundaries."""

from __future__ import annotations

import argparse
from automation_common import ACTION_PATH, POLICY_PATH, ROOT, WORKFLOW_PATH, load, validate_catalogs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    catalog = load(ROOT / "docs/zero-trust/capability-catalog.yaml")
    errors = validate_catalogs(load(ACTION_PATH), load(WORKFLOW_PATH), load(POLICY_PATH), {item["id"] for item in catalog["capabilities"]})
    if errors:
        for error in errors: print(f"[FAIL] {error}")
        print(f"Summary: 0 PASS / 0 WARN / {len(errors)} FAIL")
        return 1
    print("[PASS] Automation integration inventory, action catalog, workflow graph, approval policy, and fixed-handler boundary are consistent.")
    print("Summary: 1 PASS / 0 WARN / 0 FAIL")
    return 0


if __name__ == "__main__": raise SystemExit(main())
